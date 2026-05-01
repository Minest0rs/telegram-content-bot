"""Web search via DuckDuckGo (free, no API key)."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from src.core.logging import get_logger
from src.services.collectors.base import CollectedItem, Period

logger = get_logger(__name__)

_DDG_TIMERANGE: dict[Period, str] = {
    "hour": "d",  # ddgs has no <day granularity; "d" = past day
    "day": "d",
    "week": "w",
    "month": "m",
}


async def collect_web_search(
    query: str,
    *,
    period: Period = "day",
    max_results: int = 10,
) -> list[CollectedItem]:
    """Run a DuckDuckGo text search and convert hits to ``CollectedItem``."""

    def _search() -> list[dict[str, Any]]:
        try:
            from ddgs import DDGS
        except ImportError:  # pragma: no cover
            logger.warning("ddgs.import_failed")
            return []

        with DDGS() as ddgs:
            try:
                results = ddgs.text(
                    query,
                    timelimit=_DDG_TIMERANGE.get(period, "d"),
                    max_results=max_results,
                )
                return list(results) if results else []
            except Exception as exc:
                logger.warning("ddgs.search_failed", error=str(exc))
                return []

    raw = await asyncio.to_thread(_search)
    items: list[CollectedItem] = []
    for r in raw:
        items.append(
            CollectedItem(
                title=cast(str, r.get("title") or ""),
                url=cast(str | None, r.get("href") or r.get("url")),
                text=cast(str, r.get("body") or ""),
                source="web",
            )
        )
    return items
