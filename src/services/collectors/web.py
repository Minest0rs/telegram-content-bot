"""Web search via DuckDuckGo (free, no API key)."""

from __future__ import annotations

import asyncio
from typing import Any, cast

import httpx
from bs4 import BeautifulSoup

from src.core.logging import get_logger
from src.services.collectors.base import CollectedItem, Period

logger = get_logger(__name__)

_FETCH_TIMEOUT = httpx.Timeout(6.0, connect=4.0)
_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru,en;q=0.9",
}
_PAGE_TEXT_LIMIT = 2000  # chars
_FETCH_TOP_N = 5  # how many top results to enrich with full-page text

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
    max_results: int = 15,
) -> list[CollectedItem]:
    """Run a DuckDuckGo text search and convert hits to ``CollectedItem``.

    We first try a time-restricted search (matching ``period``) and, if it
    yields too few hits, fall back to an unrestricted search. This handles
    "evergreen" topics (e.g. "best pastry chefs") that have very few fresh
    pages but plenty of solid older ones.
    """

    def _do_search(timelimit: str | None) -> list[dict[str, Any]]:
        try:
            from ddgs import DDGS
        except ImportError:  # pragma: no cover
            logger.warning("ddgs.import_failed")
            return []

        with DDGS() as ddgs:
            try:
                kwargs: dict[str, Any] = {"max_results": max_results}
                if timelimit:
                    kwargs["timelimit"] = timelimit
                results = ddgs.text(query, **kwargs)
                return list(results) if results else []
            except Exception as exc:
                logger.warning(
                    "ddgs.search_failed",
                    error=str(exc),
                    timelimit=timelimit,
                )
                return []

    def _search() -> list[dict[str, Any]]:
        primary = _do_search(_DDG_TIMERANGE.get(period))
        if len(primary) >= 5:
            return primary
        # Fallback: drop the time filter to surface evergreen sources.
        broad = _do_search(None)
        return broad if len(broad) > len(primary) else primary

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

    # Enrich the top N items with the actual article text. ddgs only returns
    # short SEO snippets — useless for a writer model — so we follow the URL
    # and extract the readable body text. Done in parallel with a short
    # timeout; if a fetch fails, the original snippet is kept.
    enrich_targets = [it for it in items[:_FETCH_TOP_N] if it.url]
    if enrich_targets:
        async with httpx.AsyncClient(
            timeout=_FETCH_TIMEOUT,
            headers=_FETCH_HEADERS,
            follow_redirects=True,
        ) as client:
            results = await asyncio.gather(
                *(_fetch_text(client, it.url or "") for it in enrich_targets),
                return_exceptions=True,
            )
        for item, fetched in zip(enrich_targets, results, strict=True):
            if isinstance(fetched, str) and len(fetched) > len(item.text):
                item.text = fetched

    return items


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str:
    """Download ``url`` and return up to ``_PAGE_TEXT_LIMIT`` chars of body
    text. Returns an empty string on any failure."""
    try:
        resp = await client.get(url)
    except Exception as exc:
        logger.debug("web.fetch_failed", url=url, error=str(exc))
        return ""
    if resp.status_code >= 400:
        return ""
    ct = resp.headers.get("content-type", "")
    if "html" not in ct.lower() and "xml" not in ct.lower():
        return ""
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception:
        return ""
    # Strip noise.
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    # Prefer <article> / <main> as the content root.
    root = soup.find("article") or soup.find("main") or soup.body or soup
    paragraphs: list[str] = []
    for el in root.find_all(["p", "h1", "h2", "h3", "li"]):
        txt = " ".join(el.get_text(" ", strip=True).split())
        if len(txt) >= 40:  # skip nav links / tiny snippets
            paragraphs.append(txt)
        if sum(len(p) for p in paragraphs) >= _PAGE_TEXT_LIMIT:
            break
    text = "\n".join(paragraphs)
    return text[:_PAGE_TEXT_LIMIT]
