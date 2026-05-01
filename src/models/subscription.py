"""Subscription model and tier definitions."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User


class SubscriptionTier(enum.StrEnum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


@dataclass(frozen=True)
class TierFeatures:
    """Capability flags + quotas per tier."""

    monthly_post_limit: int  # -1 means unlimited
    can_generate_images: bool
    can_use_custom_prompt: bool
    can_analyze_channel_style: bool
    has_watermark: bool
    in_channel_promo_every_n_posts: int  # 0 disables promo posts
    price_stars: int  # Telegram Stars; 0 = free


TIER_FEATURES: dict[SubscriptionTier, TierFeatures] = {
    SubscriptionTier.FREE: TierFeatures(
        monthly_post_limit=3,
        can_generate_images=False,
        can_use_custom_prompt=False,
        can_analyze_channel_style=False,
        has_watermark=True,
        in_channel_promo_every_n_posts=5,
        price_stars=0,
    ),
    SubscriptionTier.PRO: TierFeatures(
        monthly_post_limit=50,
        can_generate_images=True,
        can_use_custom_prompt=False,
        can_analyze_channel_style=False,
        has_watermark=True,
        in_channel_promo_every_n_posts=0,
        price_stars=100,
    ),
    SubscriptionTier.PREMIUM: TierFeatures(
        monthly_post_limit=-1,
        can_generate_images=True,
        can_use_custom_prompt=True,
        can_analyze_channel_style=True,
        has_watermark=False,
        in_channel_promo_every_n_posts=0,
        price_stars=500,
    ),
}


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    tier: Mapped[SubscriptionTier] = mapped_column(
        SAEnum(
            SubscriptionTier,
            name="subscription_tier",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=SubscriptionTier.FREE,
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    posts_used_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    promo_post_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="subscription")

    @property
    def features(self) -> TierFeatures:
        return TIER_FEATURES[self.tier]

    @property
    def is_active(self) -> bool:
        if self.tier == SubscriptionTier.FREE:
            return True
        if self.expires_at is None:
            return False
        return self.expires_at > datetime.now(self.expires_at.tzinfo)

    def remaining_posts(self) -> int:
        limit = self.features.monthly_post_limit
        if limit < 0:
            return 10**9
        return max(0, limit - self.posts_used_this_month)

    def __repr__(self) -> str:
        return f"<Subscription user={self.user_id} tier={self.tier.value}>"
