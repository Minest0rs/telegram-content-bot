"""Free image generation via Pollinations.ai (no API key)."""

from __future__ import annotations

from urllib.parse import quote

from src.services.images.base import ImageResult


async def generate_pollinations(
    prompt: str,
    *,
    width: int = 1024,
    height: int = 768,
    nologo: bool = True,
    seed: int | None = None,
) -> ImageResult:
    """Build a Pollinations.ai image URL.

    The Pollinations service generates the image on-demand when the URL is
    fetched, so we just construct the URL — Telegram will fetch it directly.
    """
    encoded = quote(prompt, safe="")
    params = [f"width={width}", f"height={height}"]
    if nologo:
        params.append("nologo=true")
    if seed is not None:
        params.append(f"seed={seed}")
    query = "&".join(params)
    url = f"https://image.pollinations.ai/prompt/{encoded}?{query}"
    return ImageResult(url=url, source="pollinations", credit=None)
