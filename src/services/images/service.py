"""High-level image picker: stocks first, fallback to Pollinations."""

from __future__ import annotations

from src.core.logging import get_logger
from src.services.images.base import ImageResult
from src.services.images.pollinations import generate_pollinations
from src.services.images.stocks import search_pexels, search_unsplash

logger = get_logger(__name__)


async def find_image(
    query: str,
    *,
    allow_generation: bool = True,
) -> ImageResult | None:
    """Try Unsplash, then Pexels, then Pollinations (if allowed)."""
    if not query.strip():
        return None

    for func in (search_unsplash, search_pexels):
        try:
            result = await func(query)
        except Exception as exc:
            logger.warning("image.stock_failed", source=func.__name__, error=str(exc))
            result = None
        if result is not None:
            return result

    if allow_generation:
        try:
            return await generate_pollinations(query)
        except Exception as exc:
            logger.warning("image.gen_failed", error=str(exc))
            return None

    return None
