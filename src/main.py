"""Bot entry point."""

from __future__ import annotations

import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.handlers import get_root_router
from src.bot.middleware import DatabaseMiddleware, UserMiddleware
from src.core.config import settings
from src.core.db import dispose_engine
from src.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


def _build_storage() -> MemoryStorage | RedisStorage:
    try:
        return RedisStorage.from_url(settings.redis_url)
    except Exception as exc:
        logger.warning("storage.redis_unavailable", error=str(exc))
        return MemoryStorage()


async def _on_startup(bot: Bot) -> None:
    me = await bot.get_me()
    logger.info("bot.started", username=me.username, id=me.id)


async def main() -> None:
    setup_logging()

    if not settings.bot_token.get_secret_value():
        logger.error("bot.token_missing")
        print(
            "BOT_TOKEN is not set. Get one from @BotFather and add it to .env",
            file=sys.stderr,
        )
        return

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    storage = _build_storage()
    dp = Dispatcher(storage=storage)

    # outer middlewares (run before filters): db -> user.
    # Bind to message + callback_query observers so the middleware sees the
    # concrete event (with .from_user) rather than the wrapping Update.
    db_mw = DatabaseMiddleware()
    user_mw = UserMiddleware()
    for observer in (dp.message, dp.callback_query, dp.pre_checkout_query):
        observer.outer_middleware(db_mw)
        observer.outer_middleware(user_mw)

    dp.include_router(get_root_router())
    dp.startup.register(_on_startup)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
