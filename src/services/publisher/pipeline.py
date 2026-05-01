"""End-to-end post generation pipeline."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from src.core.logging import get_logger
from src.models import Source, SourceType, SubscriptionTier
from src.services.ai import ChatMessage, get_provider
from src.services.collectors import (
    CollectedItem,
    Period,
    collect_rss,
    collect_telegram_channel,
    collect_web_search,
)
from src.services.images import ImageResult, find_image

logger = get_logger(__name__)

_DEFAULT_SYSTEM_PROMPT = """\
You write engaging, well-structured posts for a Telegram channel.

Constraints:
- 1-4 short paragraphs
- friendly but informative tone
- use 1-3 emoji where appropriate
- end with 2-4 relevant hashtags
- write in the same language as the source material (Russian if Russian sources, English if English, etc.)
- do NOT invent facts; rely only on the supplied source snippets
- if the sources contradict each other, mention that briefly
"""

_USER_PROMPT_TEMPLATE = """\
Topic: {topic}
Time period: {period}

{style_block}Write a single Telegram post (with HTML formatting allowed: <b>, <i>, <u>, <s>, <code>) based on the snippets below.
Do NOT include source URLs. Do NOT include the words "Sources:" or any footer.

SOURCES:
{sources}
"""


@dataclass
class GenerateRequest:
    user_id: int
    topic: str | None
    period: Period
    sources: list[Source]
    locale: str = "ru"
    tier: SubscriptionTier = SubscriptionTier.FREE
    custom_system_prompt: str | None = None
    channel_style: str | None = None
    want_image: bool = True


@dataclass
class GenerateResult:
    body_text: str
    image: ImageResult | None
    collected: list[CollectedItem] = field(default_factory=list)


async def _collect(sources: list[Source], period: Period, topic: str | None) -> list[CollectedItem]:
    """Run all enabled sources in parallel and collect their items."""
    coros: list[asyncio.Future[list[CollectedItem]]] = []
    for src in sources:
        if not src.enabled:
            continue
        if src.type == SourceType.WEB:
            query = src.value if not topic else f"{src.value} {topic}".strip()
            coros.append(asyncio.ensure_future(collect_web_search(query, period=period)))
        elif src.type == SourceType.RSS:
            coros.append(asyncio.ensure_future(collect_rss(src.value, period=period)))
        elif src.type == SourceType.TELEGRAM:
            coros.append(asyncio.ensure_future(collect_telegram_channel(src.value, period=period)))

    if not coros:
        return []

    results = await asyncio.gather(*coros, return_exceptions=True)
    items: list[CollectedItem] = []
    for r in results:
        if isinstance(r, BaseException):
            logger.warning("collect.exception", error=str(r))
            continue
        items.extend(r)
    return items


def _build_messages(req: GenerateRequest, items: list[CollectedItem]) -> list[ChatMessage]:
    system_prompt = req.custom_system_prompt or _DEFAULT_SYSTEM_PROMPT
    style_block = ""
    if req.channel_style:
        style_block = (
            "Match this channel's writing style:\n"
            f"<style_guide>\n{req.channel_style}\n</style_guide>\n\n"
        )
    sources_text = "\n".join(item.to_prompt_line() for item in items[:25]) or "(none)"
    user = _USER_PROMPT_TEMPLATE.format(
        topic=req.topic or "(open — pick the most interesting angle)",
        period=req.period,
        style_block=style_block,
        sources=sources_text,
    )
    return [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=user),
    ]


async def _pick_image_query(req: GenerateRequest, body_text: str) -> str:
    """Ask the AI for a good 3-6 word image search query for the post."""
    provider = get_provider()
    try:
        query = await provider.complete(
            [
                ChatMessage(
                    role="system",
                    content=(
                        "Return only a 3-6 word English image search query that captures "
                        "the post's main visual subject. No quotes, no punctuation."
                    ),
                ),
                ChatMessage(role="user", content=body_text[:1500]),
            ],
            temperature=0.3,
            max_tokens=40,
        )
    except Exception:
        query = req.topic or ""
    query = query.strip().strip(".\"'`").splitlines()[0] if query else ""
    return query or (req.topic or "")


async def generate_post(req: GenerateRequest) -> GenerateResult:
    """Run the full pipeline. Does NOT apply watermark or publish — caller does that."""
    items = await _collect(req.sources, req.period, req.topic)
    if not items and not req.topic:
        # without sources or a topic, we have nothing to write about
        raise RuntimeError("No source items and no topic; cannot generate a post.")

    provider = get_provider()
    messages = _build_messages(req, items)
    body = await provider.complete(messages, temperature=0.7, max_tokens=1200)

    image: ImageResult | None = None
    if req.want_image:
        query = await _pick_image_query(req, body)
        image = await find_image(query, allow_generation=True)

    return GenerateResult(body_text=body, image=image, collected=items)
