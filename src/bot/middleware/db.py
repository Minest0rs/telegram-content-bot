"""Inject an SQLAlchemy session into handler context."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.core.db import session_scope


class DatabaseMiddleware(BaseMiddleware):
    """Provide ``session`` to handlers and commit at the end."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with session_scope() as session:
            data["session"] = session
            return await handler(event, data)
