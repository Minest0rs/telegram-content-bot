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
You write Telegram channel posts. NOT Wikipedia entries, NOT essays,
NOT chat replies — actual Telegram posts that real subscribers want
to read.

HARD RULES (override everything else):
- Output language: {output_language}. Do NOT mix in words from other
  languages, do NOT use foreign-script characters (no Chinese,
  Japanese, Arabic, etc.) unless a proper noun in the sources requires
  it.
- Use ONLY facts from the supplied SOURCES. You may NOT add names,
  dates, statistics, or claims that are not explicitly there.
- Never hedge or apologize: no "we can only assume", "к сожалению, не
  упоминается", "perhaps", "presumably", "согласно источникам", "по
  имеющимся данным". If a source mentions something — state it as fact.
- Never write meta sentences about what the post is about: no "В мире
  ... есть множество ...", "Сегодня поговорим о ...", "Если вы
  ищете ...", "Стоит отметить, что ...". Get straight into the content.
- Never include URLs, the word "Sources", or any kind of footer.

STYLE — write like a real Telegram post:
- TOTAL length: 80-160 words. Posts longer than 200 words feel like
  articles and people scroll past.
- Open with a hook in the FIRST line — a striking fact, a number, a
  surprising claim, or a question. NOT "В мире кондитерского ...".
- Short, punchy sentences. Mix lengths. Use line breaks between
  thoughts to create rhythm.
- Have a point of view. If you're listing pastry chefs, say WHY they
  matter, not just that they exist.
- Drop the formal register. Write like an editor who actually likes the
  topic, not like a textbook.
- 1-3 emoji, placed where they actually add meaning (not after every
  sentence).
- End with 2-4 relevant hashtags on the last line. Make them readable
  (#кондитеры, not #КондитерскиеИскусство).

EXAMPLE OF THE WIKIPEDIA TONE TO AVOID (do NOT write like this):
"В мире X есть множество талантливых специалистов, которые создают
удивительные продукты. Согласно источникам, лучшими являются А, Б и
В. Если вы ищете вдохновение, вы можете посмотреть на сайтах ..."

EXAMPLES OF THE RIGHT TONE (about UNRELATED topics — do NOT copy these
facts; only the structure and rhythm):
- "Шведы доели последний ИКЕА-фрикадельку из говядины. Теперь это
  курица, чечевица или растительный белок — компания тихо переводит
  меню на «зелёное» в 2024-м.
  Причина прозаичная: ИКЕА вторая в мире сеть общепита по объёму
  закупки мяса. Цифры по углероду больше скрывать нельзя.
  #икеа #еда #экология"
- "iPhone 16 продаётся медленнее iPhone 15 — на 10% за первые недели.
  Apple винит пустой AI-релиз: Apple Intelligence не дошла до Европы,
  а в США работает только на Pro-моделях.
  Аналитики Bloomberg говорят, рост вернётся, как только функции
  доедут до всех. Если доедут.
  #эппл #айфон #технологии"
"""

_LOCALE_LANGUAGE = {
    "ru": "Russian (русский)",
    "en": "English",
    "es": "Spanish (Español)",
}


_USER_PROMPT_TEMPLATE = """\
Topic: {topic}
Time period: {period}

{style_block}Write ONE Telegram post (HTML formatting allowed: <b>, <i>, <u>, <s>, <code>) based STRICTLY on the sources below.

Reminder: do NOT add facts that aren't in these sources, and do NOT
write any apologies about missing information.

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
    output_language = _LOCALE_LANGUAGE.get(req.locale, "the source-material language")
    system_prompt_template = req.custom_system_prompt or _DEFAULT_SYSTEM_PROMPT
    # Allow custom prompts to opt out of language injection by not including
    # the placeholder.
    if "{output_language}" in system_prompt_template:
        system_prompt = system_prompt_template.format(output_language=output_language)
    else:
        system_prompt = system_prompt_template
    style_block = ""
    if req.channel_style:
        style_block = (
            "Match this channel's writing style:\n"
            f"<style_guide>\n{req.channel_style}\n</style_guide>\n\n"
        )
    sources_text = "\n\n".join(item.to_prompt_line() for item in items[:15]) or "(none)"
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
    # Lower temperature → less drift / mixed-language tokens / hedging.
    body = await complete_with_fallback(messages, temperature=0.3, max_tokens=1200)

    image: ImageResult | None = None
    if req.want_image:
        query = await _pick_image_query(req, body)
        image = await find_image(query, allow_generation=True)

    return GenerateResult(body_text=body, image=image, collected=items)
