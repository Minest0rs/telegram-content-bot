"""Resolve / create the User row for the current Telegram user, then inject it."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.models import Subscription, SubscriptionTier, User
from src.services.subscription import ensure_subscription


class UserMiddleware(BaseMiddleware):
    """Resolve or create the DB user record."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = _extract_user(event)
        session: AsyncSession | None = data.get("session")
        if tg_user is None or session is None:
            return await handler(event, data)

        user = await _get_or_create_user(session, tg_user)
        data["user"] = user
        return await handler(event, data)


def _extract_user(event: TelegramObject) -> TgUser | None:
    if isinstance(event, Message):
        return event.from_user
    if isinstance(event, CallbackQuery):
        return event.from_user
    return getattr(event, "from_user", None)


async def _get_or_create_user(session: AsyncSession, tg_user: TgUser) -> User:
    stmt = (
        select(User).options(selectinload(User.subscription)).where(User.telegram_id == tg_user.id)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            locale=_resolve_locale(tg_user),
        )
        session.add(user)
        await session.flush()
        sub = Subscription(user_id=user.id, tier=SubscriptionTier.FREE)
        session.add(sub)
        await session.flush()
        user.subscription = sub
    else:
        # keep username/first_name fresh
        changed = False
        if tg_user.username and user.username != tg_user.username:
            user.username = tg_user.username
            changed = True
        if tg_user.first_name and user.first_name != tg_user.first_name:
            user.first_name = tg_user.first_name
            changed = True
        if changed:
            await session.flush()
        await ensure_subscription(session, user)

    return user


def _resolve_locale(tg_user: TgUser) -> str:
    code = (tg_user.language_code or "").lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("es"):
        return "es"
    if code.startswith("en"):
        return "en"
    return settings.default_locale
