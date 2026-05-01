"""RSS / Atom feed collector (via feedparser)."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any, cast

from src.core.logging import get_logger
from src.services.collectors.base import CollectedItem, Period, period_to_timedelta

logger = get_logger(__name__)


def _entry_published(entry: Any) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if parsed is None:
        return None
    try:
        return datetime.fromtimestamp(time.mktime(parsed), tz=UTC)
    except (TypeError, ValueError):
        return None


async def collect_rss(
    url: str,
    *,
    period: Period = "day",
    max_results: int = 15,
) -> list[CollectedItem]:
    """Fetch an RSS feed and return entries within the requested period."""

    def _parse() -> list[CollectedItem]:
        try:
            import feedparser
        except ImportError:  # pragma: no cover
            logger.warning("feedparser.import_failed")
            return []

        try:
            feed = feedparser.parse(url, agent="telegram-content-bot/0.1")
        except Exception as exc:
            logger.warning("feedparser.parse_failed", url=url, error=str(exc))
            return []

        feed_title = cast(str, getattr(feed.feed, "title", url))
        cutoff = datetime.now(UTC) - period_to_timedelta(period)

        items: list[CollectedItem] = []
        for entry in feed.entries[: max_results * 3]:  # over-fetch to filter by date
            published = _entry_published(entry)
            if published is not None and published < cutoff:
                continue
            title = cast(str, getattr(entry, "title", "") or "")
            link = cast(str | None, getattr(entry, "link", None))
            summary = cast(str, getattr(entry, "summary", "") or "")
            content_field = getattr(entry, "content", None)
            if content_field and isinstance(content_field, list):
                summary = cast(str, content_field[0].get("value", summary))
            if not title and not summary:
                continue
            items.append(
                CollectedItem(
                    title=title,
                    url=link,
                    text=_strip_html(summary),
                    source=f"rss:{feed_title}",
                    published_at=published,
                )
            )
            if len(items) >= max_results:
                break
        return items

    return await asyncio.to_thread(_parse)


def _strip_html(text: str) -> str:
    if "<" not in text:
        return text
    try:
        from bs4 import BeautifulSoup

        return BeautifulSoup(text, "lxml").get_text(" ", strip=True)
    except ImportError:  # pragma: no cover
        return text
