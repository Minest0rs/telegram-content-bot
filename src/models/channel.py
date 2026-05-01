"""Telegram channel model (channels users have connected)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.post import Post
    from src.models.user import User


class Channel(Base, TimestampMixin):
    __tablename__ = "channels"
    __table_args__ = (UniqueConstraint("user_id", "telegram_chat_id", name="uq_channel_user_chat"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    username: Mapped[str | None] = mapped_column(String(64))
    style_summary: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship("User", back_populates="channels")
    posts: Mapped[list[Post]] = relationship(
        "Post", back_populates="channel", cascade="all, delete-orphan"
    )

    @property
    def display_name(self) -> str:
        if self.username:
            return f"@{self.username}"
        return self.title

    def __repr__(self) -> str:
        return f"<Channel id={self.id} chat={self.telegram_chat_id} title={self.title!r}>"
