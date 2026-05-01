"""Arq worker: periodic tasks (watermark scan, monthly counter reset, showcase posts)."""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import Any, ClassVar

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import update

from src.core.config import settings
from src.core.db import dispose_engine, session_scope
from src.core.i18n import i18n
from src.core.logging import get_logger, setup_logging
from src.models import Subscription
from src.services.promo import generate_showcase_post
from src.services.scanner import scan_user_channels

logger = get_logger(__name__)


async def watermark_scan(ctx: dict[str, Any]) -> None:
    """Scan user channels for missing signatures and restore them."""
    bot: Bot = ctx["bot"]
    signature_template = i18n.t("watermark.signature", locale="en", bot_username="{bot_username}")
    async with session_scope() as session:
        repaired = await scan_user_channels(bot, session, signature_template)
    if repaired:
        logger.info("watermark.scan_repaired", count=repaired)


async def reset_monthly_counters(ctx: dict[str, Any]) -> None:
    """Reset posts_used_this_month at the start of each month."""
    today = datetime.now(UTC).date()
    if today.day != 1:
        return
    async with session_scope() as session:
        await session.execute(update(Subscription).values(posts_used_this_month=0))
    logger.info("subscriptions.monthly_reset")


async def showcase_promo(ctx: dict[str, Any]) -> None:
    """Generate and post a promo to the bot's own showcase channel, if configured."""
    if not settings.bot_showcase_channel:
        return
    bot: Bot = ctx["bot"]
    text = await generate_showcase_post(language="en")
    if text is None:
        return
    me = await bot.get_me()
    text = text.replace("{bot_username}", me.username or "your_bot")
    try:
        await bot.send_message(chat_id=settings.bot_showcase_channel, text=text, parse_mode="HTML")
    except Exception as exc:
        logger.warning("promo.showcase_send_failed", error=str(exc))


async def startup(ctx: dict[str, Any]) -> None:
    setup_logging()
    ctx["bot"] = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    )


async def shutdown(ctx: dict[str, Any]) -> None:
    bot: Bot | None = ctx.get("bot")
    if bot is not None:
        await bot.session.close()
    await dispose_engine()


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = startup
    on_shutdown = shutdown
    cron_jobs: ClassVar[list[Any]] = [
        cron(watermark_scan, minute={0}),
        cron(reset_monthly_counters, hour={0}, minute={5}),
        cron(showcase_promo, hour={12}, minute={0}),
    ]
    functions: ClassVar[list[Any]] = [
        watermark_scan,
        reset_monthly_counters,
        showcase_promo,
    ]


# Unused import kept for type clarity
_ = time
