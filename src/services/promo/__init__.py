"""Self-promotion posts (in client channel + on bot's own showcase channel)."""

from src.services.promo.service import (
    generate_showcase_post,
    maybe_post_in_channel_promo,
)

__all__ = [
    "generate_showcase_post",
    "maybe_post_in_channel_promo",
]
