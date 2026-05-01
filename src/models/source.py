"""Information source (web search query, RSS feed, or TG channel)."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.models.user import User


class SourceType(enum.StrEnum):
    WEB = "web"
    RSS = "rss"
    TELEGRAM = "telegram"


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[SourceType] = mapped_column(SAEnum(SourceType, name="source_type"), nullable=False)
    # for web: search query; for rss: feed url; for telegram: @username or t.me/...
    value: Mapped[str] = mapped_column(String(512), nullable=False)
    label: Mapped[str | None] = mapped_column(String(256))
    notes: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="sources")

    def __repr__(self) -> str:
        return f"<Source id={self.id} type={self.type.value} value={self.value!r}>"
