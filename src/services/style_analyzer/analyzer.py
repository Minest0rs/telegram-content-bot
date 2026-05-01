"""Read recent channel posts via Telethon, ask the AI to summarize the style."""

from __future__ import annotations

from src.core.logging import get_logger
from src.services.ai import ChatMessage, get_provider
from src.services.collectors.telegram import _get_client

logger = get_logger(__name__)


_STYLE_PROMPT = """\
You are an editorial assistant. Below are recent posts from a Telegram channel.
Produce a concise STYLE GUIDE (4-8 bullet points) that captures:

- typical post length and structure
- tone and voice (formal/casual/sarcastic/...)
- usage of emoji, hashtags, links
- recurring rhetorical devices or phrases
- any consistent formatting (headlines, quotes, lists)

Respond in the same language the channel uses. Output the bullets only — no preamble.

POSTS:
{posts}
"""


async def _fetch_recent_messages(handle: str, limit: int = 50) -> list[str]:
    client = await _get_client()
    if client is None:
        logger.info("style_analyzer.no_telethon")
        return []
    handle = handle.strip()
    if handle.startswith("https://t.me/"):
        handle = "@" + handle.removeprefix("https://t.me/").split("/")[0]
    if handle.startswith("t.me/"):
        handle = "@" + handle.removeprefix("t.me/").split("/")[0]

    msgs: list[str] = []
    try:
        async for msg in client.iter_messages(handle, limit=limit):
            text = (msg.text or msg.message or "").strip()
            if text:
                msgs.append(text)
    except Exception as exc:
        logger.warning("style_analyzer.fetch_failed", handle=handle, error=str(exc))
    return msgs


async def analyze_channel_style(channel_handle: str, *, limit: int = 50) -> str | None:
    """Return a textual style summary, or None if not enough data / Telethon unavailable."""
    messages = await _fetch_recent_messages(channel_handle, limit=limit)
    if len(messages) < 5:
        return None
    joined = "\n\n---\n\n".join(messages[:limit])

    provider = get_provider()
    style = await provider.complete(
        [
            ChatMessage(role="system", content="You are a precise editorial assistant."),
            ChatMessage(role="user", content=_STYLE_PROMPT.format(posts=joined)),
        ],
        temperature=0.3,
        max_tokens=600,
    )
    return style.strip()
