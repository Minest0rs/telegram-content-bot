"""Self-promotion logic.

Two flavors:

1. **In-channel promo:** every Nth post in a free-tier user's channel, the bot
   appends/sends a small "I'm an AI bot, try me" promo.

2. **Showcase channel:** the bot's own marketing channel — periodically a
   worker generates a promo post and publishes it.
"""

from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.i18n import i18n
from src.core.logging import get_logger
from src.models import Subscription
from src.services.ai import ChatMessage, get_provider

logger = get_logger(__name__)

_SHOWCASE_PROMPT = """\
Write a short, lively Telegram post (2-3 short paragraphs) advertising an AI
content-creation bot to channel admins. Highlight ONE of these features
(rotate randomly): automatic news collection, channel-style mimicry,
multi-language support, image generation, time-period filtering, or
subscription tiers. End with: "Try it: @{bot_username}".

Use the same language as the channel: {language}.
Add 2-3 relevant hashtags.
Do NOT mention competitors. Do NOT use a generic "I'm an AI" disclaimer.
"""


async def maybe_post_in_channel_promo(
    bot: Bot,
    *,
    chat_id: int,
    locale: str,
    subscription: Subscription,
) -> bool:
    """If it's time, send a one-off promo message to the user's channel.

    Returns True if a promo was sent.
    """
    feat = subscription.features
    if feat.in_channel_promo_every_n_posts <= 0:
        return False
    if subscription.promo_post_counter < feat.in_channel_promo_every_n_posts:
        return False

    me = await bot.get_me()
    text = i18n.t("promo.in_channel", locale=locale, bot_username=me.username or "")
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    except Exception as exc:
        logger.warning("promo.in_channel_failed", chat_id=chat_id, error=str(exc))
        return False

    subscription.promo_post_counter = 0
    return True


async def generate_showcase_post(language: str = "en") -> str | None:
    """Generate a promo post for the bot's own showcase channel."""
    if not settings.bot_showcase_channel:
        return None
    provider = get_provider()
    try:
        text = await provider.complete(
            [
                ChatMessage(
                    role="system",
                    content="You are a marketing copywriter for AI products.",
                ),
                ChatMessage(
                    role="user",
                    content=_SHOWCASE_PROMPT.format(
                        bot_username="{bot_username}", language=language
                    ),
                ),
            ],
            temperature=0.85,
            max_tokens=600,
        )
        return text.strip()
    except Exception as exc:
        logger.warning("promo.showcase_gen_failed", error=str(exc))
        return None


__all__ = [
    "generate_showcase_post",
    "maybe_post_in_channel_promo",
]


# unused import kept intentionally for future use of session-aware promo logging
_ = AsyncSession
