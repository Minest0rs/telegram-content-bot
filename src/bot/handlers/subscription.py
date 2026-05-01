"""Subscription menu handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import subscription_kb
from src.core.i18n import i18n
from src.models import SubscriptionTier, User
from src.models.subscription import TIER_FEATURES
from src.services.payments import build_invoice_payload
from src.services.subscription import ensure_subscription

router = Router(name="subscription")


@router.callback_query(F.data == "menu:subscription")
async def cb_menu_subscription(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    sub = await ensure_subscription(session, user)
    feat = sub.features
    limit = feat.monthly_post_limit if feat.monthly_post_limit >= 0 else "∞"
    text = i18n.t(
        "subscription.tiers",
        locale=user.locale,
        current=sub.tier.value,
        used=sub.posts_used_this_month,
        limit=limit,
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text, reply_markup=subscription_kb(user.locale), parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:buy:"))
async def cb_buy(callback: CallbackQuery, user: User) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    tier_value = parts[2]
    try:
        tier = SubscriptionTier(tier_value)
    except ValueError:
        await callback.answer()
        return

    feat = TIER_FEATURES[tier]
    if feat.price_stars <= 0:
        await callback.answer("Free tier is, well, free.")
        return

    title = f"{tier.value.capitalize()} — 30 days"
    description = (
        f"Subscribe to {tier.value} for 30 days.\n"
        f"{feat.monthly_post_limit if feat.monthly_post_limit >= 0 else '∞'} posts/month, "
        f"{'image gen, ' if feat.can_generate_images else ''}"
        f"{'custom prompt, ' if feat.can_use_custom_prompt else ''}"
        f"{'channel style analysis' if feat.can_analyze_channel_style else 'no extras'}."
    )
    payload = build_invoice_payload(user_id=user.telegram_id, tier=tier, duration_days=30)

    bot = callback.bot
    if bot is None:
        await callback.answer()
        return
    await bot.send_invoice(
        chat_id=user.telegram_id,
        title=title,
        description=description,
        payload=payload,
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=title, amount=feat.price_stars)],
        provider_token="",  # Stars don't need a provider token
    )
    await callback.answer()
