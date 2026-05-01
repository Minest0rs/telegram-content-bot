"""Handle Telegram Stars payment confirmations."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message, PreCheckoutQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import main_menu_kb
from src.core.i18n import i18n
from src.core.logging import get_logger
from src.models import User
from src.services.payments import parse_invoice_payload
from src.services.subscription import upgrade_to_tier

logger = get_logger(__name__)
router = Router(name="payments")


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    payload = parse_invoice_payload(query.invoice_payload or "")
    if payload is None:
        await query.answer(ok=False, error_message="Invalid invoice")
        return
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, session: AsyncSession) -> None:
    sp = message.successful_payment
    if sp is None or message.from_user is None:
        return

    payload = parse_invoice_payload(sp.invoice_payload or "")
    if payload is None:
        logger.warning("payments.bad_payload", payload=sp.invoice_payload)
        return

    result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
    user = result.scalar_one_or_none()
    if user is None:
        logger.warning("payments.user_missing", tg_id=message.from_user.id)
        return

    bot = message.bot
    assert bot is not None
    sub = await upgrade_to_tier(
        session,
        bot=bot,
        user=user,
        tier=payload.tier,
        duration_days=payload.duration_days,
    )
    until = sub.expires_at.strftime("%Y-%m-%d") if sub.expires_at else "—"
    await message.answer(
        i18n.t(
            "subscription.bought",
            locale=user.locale,
            tier=payload.tier.value,
            until=until,
        ),
        reply_markup=main_menu_kb(user.locale),
        parse_mode="HTML",
    )
