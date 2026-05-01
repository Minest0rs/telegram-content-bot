"""Walk recent posts and re-apply the watermark when a free-tier user removed it."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models import Post, PostStatus, SubscriptionTier, User
from src.services.watermark import (
    SIGNATURE_DELIMITER,
    apply_watermark,
    has_visible_signature,
)

logger = get_logger(__name__)

# Telegram only lets bots edit messages they sent within 48 hours
EDIT_WINDOW = timedelta(hours=47, minutes=30)


async def scan_user_channels(bot: Bot, session: AsyncSession, signature_template: str) -> int:
    """Iterate published posts, restore signatures where missing.

    Returns the number of posts that were re-watermarked.

    ``signature_template`` should contain ``{bot_username}`` so we can render the
    correct signature per bot account.
    """
    cutoff = datetime.now(UTC) - EDIT_WINDOW
    stmt = (
        select(Post, User)
        .join(User, Post.user_id == User.id)
        .where(Post.status == PostStatus.PUBLISHED)
        .where(Post.has_watermark.is_(True))
        .where(Post.published_at >= cutoff)
    )
    result = await session.execute(stmt)
    rows = result.all()

    me = await bot.get_me()
    signature = signature_template.format(bot_username=me.username or "your_bot")
    repaired = 0

    for post, user in rows:
        if user.subscription is None or user.subscription.tier != SubscriptionTier.FREE:
            continue
        if post.channel is None or post.telegram_message_id is None:
            continue

        try:
            # We can't read the current text via Bot API directly; we *try* to
            # re-edit. If the live message already matches our stored text the
            # API will reject it ("message is not modified") — that's fine.
            new_text = apply_watermark(
                _strip_signature(post.body_text),
                signature=signature,
                marker_value=post.id,
            )
            await bot.edit_message_text(
                text=new_text,
                chat_id=post.channel.telegram_chat_id,
                message_id=post.telegram_message_id,
                parse_mode="HTML",
            )
            post.body_text = new_text
            repaired += 1
        except TelegramBadRequest as exc:
            msg = str(exc)
            if "message is not modified" in msg or "message to edit not found" in msg:
                continue
            logger.warning(
                "scanner.edit_failed",
                post_id=post.id,
                chat_id=post.channel.telegram_chat_id,
                error=msg,
            )

    if repaired:
        await session.commit()
    return repaired


def _strip_signature(text: str) -> str:
    if SIGNATURE_DELIMITER not in text:
        return text
    return text.split(SIGNATURE_DELIMITER, 1)[0]


__all__ = ["has_visible_signature", "scan_user_channels"]
