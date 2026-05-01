"""Stock image search via Unsplash and Pexels."""

from __future__ import annotations

import httpx

from src.core.config import settings
from src.core.logging import get_logger
from src.services.images.base import ImageResult

logger = get_logger(__name__)


async def search_unsplash(query: str) -> ImageResult | None:
    if settings.unsplash_access_key is None or not settings.unsplash_access_key.get_secret_value():
        return None
    headers = {
        "Authorization": f"Client-ID {settings.unsplash_access_key.get_secret_value()}",
        "Accept-Version": "v1",
    }
    params = {"query": query, "per_page": "1", "orientation": "landscape"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
        results = data.get("results") or []
        if not results:
            return None
        photo = results[0]
        url = photo["urls"].get("regular") or photo["urls"].get("full")
        author = photo.get("user", {}).get("name")
        return ImageResult(
            url=url,
            source="unsplash",
            credit=f"Photo by {author} on Unsplash" if author else "Unsplash",
        )
    except Exception as exc:
        logger.warning("unsplash.search_failed", query=query, error=str(exc))
        return None


async def search_pexels(query: str) -> ImageResult | None:
    if settings.pexels_api_key is None or not settings.pexels_api_key.get_secret_value():
        return None
    headers = {"Authorization": settings.pexels_api_key.get_secret_value()}
    params = {"query": query, "per_page": "1", "orientation": "landscape"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.pexels.com/v1/search",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
        photos = data.get("photos") or []
        if not photos:
            return None
        photo = photos[0]
        src = photo.get("src", {})
        url = src.get("large") or src.get("original")
        photographer = photo.get("photographer")
        return ImageResult(
            url=url,
            source="pexels",
            credit=f"Photo by {photographer} on Pexels" if photographer else "Pexels",
        )
    except Exception as exc:
        logger.warning("pexels.search_failed", query=query, error=str(exc))
        return None
