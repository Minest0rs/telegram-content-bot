"""Information collectors."""

from src.services.collectors.base import CollectedItem, Period
from src.services.collectors.rss import collect_rss
from src.services.collectors.telegram import collect_telegram_channel
from src.services.collectors.web import collect_web_search

__all__ = [
    "CollectedItem",
    "Period",
    "collect_rss",
    "collect_telegram_channel",
    "collect_web_search",
]
