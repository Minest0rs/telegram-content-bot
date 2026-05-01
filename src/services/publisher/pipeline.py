"""End-to-end post generation pipeline."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from src.core.logging import get_logger
from src.models import Source, SourceType, SubscriptionTier
from src.services.ai import ChatMessage, complete_with_fallback
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

HARD RULES — these override anything else:
- Use ONLY the supplied source snippets below as your facts. You are NOT
  allowed to add facts, names, dates, statistics, or claims that are not
  explicitly present in the snippets.
- If the snippets are too thin or off-topic to answer the prompt, write a
  short post that paraphrases what the snippets DO say — never fall back
  to general knowledge to fill the gap.
- Quote concrete details from the snippets (specific names, numbers, dates,
  events) where they exist; do not generalize them away.
- Do NOT include URLs, the word "Sources", or any kind of footer.

Style:
- 1-4 short paragraphs
- friendly but informative tone
- 1-3 emoji where appropriate
- end with 2-4 relevant hashtags
- write in the same language as the source material (Russian if the
  snippets are Russian, English if English, etc.)
- if the snippets contradict each other, mention that briefly
"""

_USER_PROMPT_TEMPLATE = """\
Topic: {topic}
Time period: {period}

{style_block}Write ONE Telegram post (HTML formatting allowed: <b>, <i>, <u>, <s>, <code>) based STRICTLY on the snippets below.

Reminder: do NOT add facts that aren't in these snippets.

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
    """Run all enabled sources in parallel and collect their items.

    Web search is implicit: when a ``topic`` is given, we always run a web
    search for it (in addition to any configured RSS / TG sources). This
    keeps the UX simple — the user types one topic at post-creation time
    and doesn't have to re-enter it as a "web source query" first.
    """
    coros: list[asyncio.Future[list[CollectedItem]]] = []
    web_queries_seen: set[str] = set()

    if topic:
        coros.append(asyncio.ensure_future(collect_web_search(topic, period=period)))
        web_queries_seen.add(topic.strip().lower())

    for src in sources:
        if not src.enabled:
            continue
        if src.type == SourceType.WEB:
            query = src.value if not topic else f"{src.value} {topic}".strip()
            key = query.strip().lower()
            if key and key not in web_queries_seen:
                web_queries_seen.add(key)
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
    try:
        query = await complete_with_fallback(
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

    messages = _build_messages(req, items)
    body = await complete_with_fallback(messages, temperature=0.7, max_tokens=1200)

    image: ImageResult | None = None
    if req.want_image:
        query = await _pick_image_query(req, body)
        image = await find_image(query, allow_generation=True)

    return GenerateResult(body_text=body, image=image, collected=items)
