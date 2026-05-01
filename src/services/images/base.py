"""Common types for the image module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ImageSource = Literal["unsplash", "pexels", "pollinations", "none"]


@dataclass(frozen=True)
class ImageResult:
    url: str
    source: ImageSource
    credit: str | None = None  # author/source attribution if needed
