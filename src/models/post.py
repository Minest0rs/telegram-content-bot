"""Generated posts and their published state."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.channel import Channel
    from src.models.user import User


class PostStatus(enum.StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id", ondelete="SET NULL"))

    status: Mapped[PostStatus] = mapped_column(
        SAEnum(PostStatus, name="post_status"),
        default=PostStatus.DRAFT,
        nullable=False,
    )
    topic: Mapped[str | None] = mapped_column(String(512))
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1024))
    image_source: Mapped[str | None] = mapped_column(String(64))  # unsplash/pexels/pollinations
    has_watermark: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_promo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # populated after publication
    telegram_message_id: Mapped[int | None] = mapped_column(BigInteger)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship("User", back_populates="posts")
    channel: Mapped[Channel | None] = relationship("Channel", back_populates="posts")

    def __repr__(self) -> str:
        return f"<Post id={self.id} status={self.status.value} channel={self.channel_id}>"
