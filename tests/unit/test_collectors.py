"""Smoke tests for collectors (no real network)."""

from __future__ import annotations

from src.services.collectors.base import (
    CollectedItem,
    period_to_timedelta,
)


def test_period_to_timedelta() -> None:
    assert period_to_timedelta("hour").total_seconds() == 3600
    assert period_to_timedelta("day").total_seconds() == 86400
    assert period_to_timedelta("week").days == 7
    assert period_to_timedelta("month").days == 30


def test_collected_item_to_prompt_line_truncates_long_text() -> None:
    item = CollectedItem(
        title="Title",
        url="https://example.com",
        text="x" * 2000,
        source="web",
    )
    line = item.to_prompt_line(max_text=200)
    assert line.startswith("- [web] Title")
    assert "https://example.com" in line
    # ensure we truncated
    assert "..." in line


def test_collected_item_handles_no_url() -> None:
    item = CollectedItem(
        title="No URL Item",
        url=None,
        text="body",
        source="rss",
    )
    line = item.to_prompt_line()
    assert "No URL Item" in line
    assert "(None)" not in line
