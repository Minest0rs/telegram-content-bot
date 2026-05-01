"""Common types for content collectors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

Period = Literal["hour", "day", "week", "month"]


def period_to_timedelta(period: Period) -> timedelta:
    return {
        "hour": timedelta(hours=1),
        "day": timedelta(days=1),
        "week": timedelta(weeks=1),
        "month": timedelta(days=30),
    }[period]


@dataclass(slots=True)
class CollectedItem:
    title: str
    url: str | None
    text: str
    source: str
    published_at: datetime | None = None

    def to_prompt_line(self, max_text: int = 1500) -> str:
        snippet = self.text.strip().replace("\n", " ")
        if len(snippet) > max_text:
            snippet = snippet[:max_text].rsplit(" ", 1)[0] + "..."
        url_part = f" ({self.url})" if self.url else ""
        return f"- [{self.source}] {self.title}{url_part}\n  {snippet}"
