"""User model."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.channel import Channel
    from src.models.post import Post
    from src.models.source import Source
    from src.models.subscription import Subscription


class PublishMode(enum.StrEnum):
    """How the bot publishes generated posts."""

    AUTO = "auto"
    PREVIEW = "preview"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    locale: Mapped[str] = mapped_column(String(8), default="ru", nullable=False)
    publish_mode: Mapped[PublishMode] = mapped_column(
        SAEnum(
            PublishMode,
            name="publish_mode",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        default=PublishMode.PREVIEW,
        nullable=False,
    )
    custom_system_prompt: Mapped[str | None] = mapped_column(Text)

    channels: Mapped[list[Channel]] = relationship(
        "Channel", back_populates="user", cascade="all, delete-orphan"
    )
    sources: Mapped[list[Source]] = relationship(
        "Source", back_populates="user", cascade="all, delete-orphan"
    )
    posts: Mapped[list[Post]] = relationship(
        "Post", back_populates="user", cascade="all, delete-orphan"
    )
    subscription: Mapped[Subscription | None] = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id} @{self.username}>"
