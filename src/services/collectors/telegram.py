"""Telegram channel collector via Telethon.

Uses a single shared client; connects lazily.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.core.config import settings
from src.core.logging import get_logger
from src.services.collectors.base import CollectedItem, Period, period_to_timedelta

if TYPE_CHECKING:
    from telethon import TelegramClient

logger = get_logger(__name__)

_client: Any | None = None
_client_lock = asyncio.Lock()


async def _get_client() -> TelegramClient | None:
    """Return a connected Telethon client, or None if Telethon is unconfigured."""
    global _client
    if not settings.has_telethon:
        return None
    async with _client_lock:
        if _client is not None:
            return _client
        try:
            from telethon import TelegramClient
        except ImportError:  # pragma: no cover
            logger.warning("telethon.import_failed")
            return None

        assert settings.telegram_api_id is not None
        assert settings.telegram_api_hash is not None
        client = TelegramClient(
            f"sessions/{settings.telegram_session_name}",
            settings.telegram_api_id,
            settings.telegram_api_hash.get_secret_value(),
        )
        try:
            await client.connect()
        except Exception as exc:  # pragma: no cover
            logger.warning("telethon.connect_failed", error=str(exc))
            return None
        _client = client
        return client


async def collect_telegram_channel(
    channel: str,
    *,
    period: Period = "day",
    max_results: int = 15,
) -> list[CollectedItem]:
    """Fetch recent messages from a public Telegram channel by @username or URL."""
    client = await _get_client()
    if client is None:
        logger.info("telethon.not_configured")
        return []

    cutoff = datetime.now(UTC) - period_to_timedelta(period)
    handle = channel.strip()
    if handle.startswith("https://t.me/"):
        handle = "@" + handle.removeprefix("https://t.me/").split("/")[0]
    if handle.startswith("t.me/"):
        handle = "@" + handle.removeprefix("t.me/").split("/")[0]

    items: list[CollectedItem] = []
    try:
        async for msg in client.iter_messages(handle, limit=max_results * 3):
            if msg.date is not None and msg.date < cutoff:
                break
            text = (msg.text or msg.message or "").strip()
            if not text:
                continue
            title = text.split("\n", 1)[0][:120]
            items.append(
                CollectedItem(
                    title=title,
                    url=f"https://t.me/{handle.lstrip('@')}/{msg.id}",
                    text=text,
                    source=f"tg:{handle}",
                    published_at=msg.date,
                )
            )
            if len(items) >= max_results:
                break
    except Exception as exc:
        logger.warning("telethon.iter_failed", channel=handle, error=str(exc))
    return items
