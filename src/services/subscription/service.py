"""Business logic around subscriptions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.models import Post, PostStatus, Subscription, SubscriptionTier, User
from src.services.watermark import strip_watermark

logger = get_logger(__name__)


async def ensure_subscription(session: AsyncSession, user: User) -> Subscription:
    """Make sure a user has a subscription row; default to FREE."""
    if user.subscription is not None:
        return user.subscription
    sub = Subscription(user_id=user.id, tier=SubscriptionTier.FREE)
    session.add(sub)
    await session.flush()
    user.subscription = sub
    return sub


async def increment_post_counter(session: AsyncSession, user: User) -> None:
    sub = await ensure_subscription(session, user)
    sub.posts_used_this_month += 1
    sub.promo_post_counter += 1
    await session.flush()


async def upgrade_to_tier(
    session: AsyncSession,
    *,
    bot: Bot,
    user: User,
    tier: SubscriptionTier,
    duration_days: int = 30,
) -> Subscription:
    """Upgrade the user's subscription and remove watermarks on existing posts.

    Per project spec:
    - On upgrade we strip the visible signature from posts published in the last
      48 hours (Bot API edit window).
    - Hidden zero-width markers are kept so the bot still recognizes its posts.
    """
    sub = await ensure_subscription(session, user)

    sub.tier = tier
    sub.expires_at = datetime.now(UTC) + timedelta(days=duration_days)
    if tier == SubscriptionTier.FREE:
        sub.expires_at = None

    if not sub.features.has_watermark:
        await _strip_watermarks_in_channel(session, bot=bot, user=user)

    await session.flush()
    return sub


async def _strip_watermarks_in_channel(session: AsyncSession, *, bot: Bot, user: User) -> None:
    """Remove visible watermark from recent published posts of the user."""
    cutoff = datetime.now(UTC) - timedelta(hours=47, minutes=30)
    stmt = (
        select(Post)
        .where(Post.user_id == user.id)
        .where(Post.status == PostStatus.PUBLISHED)
        .where(Post.has_watermark.is_(True))
        .where(Post.published_at >= cutoff)
    )
    result = await session.execute(stmt)
    posts = result.scalars().all()
    for post in posts:
        if post.channel is None or post.telegram_message_id is None:
            continue
        new_text = strip_watermark(post.body_text)
        try:
            await bot.edit_message_text(
                text=new_text,
                chat_id=post.channel.telegram_chat_id,
                message_id=post.telegram_message_id,
                parse_mode="HTML",
            )
            post.body_text = new_text
            post.has_watermark = False
        except TelegramBadRequest as exc:
            logger.warning(
                "subscription.strip_watermark_failed",
                post_id=post.id,
                error=str(exc),
            )
