"""Edit system prompt and analyze channel style."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import main_menu_kb, style_kb
from src.bot.states import EditPrompt
from src.core.i18n import i18n
from src.models import Channel, User
from src.services.style_analyzer import analyze_channel_style
from src.services.subscription import ensure_subscription

router = Router(name="style")


@router.callback_query(F.data == "menu:style")
async def cb_menu_style(callback: CallbackQuery, user: User) -> None:
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("style.title", locale=user.locale),
            reply_markup=style_kb(user.locale),
        )
    await callback.answer()


@router.callback_query(F.data == "style:edit_prompt")
async def cb_edit_prompt(
    callback: CallbackQuery, user: User, session: AsyncSession, state: FSMContext
) -> None:
    sub = await ensure_subscription(session, user)
    if not sub.features.can_use_custom_prompt:
        await callback.answer(
            i18n.t("style.system_prompt_premium_only", locale=user.locale),
            show_alert=True,
        )
        return
    await state.set_state(EditPrompt.waiting_for_text)
    current = user.custom_system_prompt or "—"
    text = i18n.t("style.system_prompt_prompt", locale=user.locale, current=current)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(EditPrompt.waiting_for_text)
async def msg_edit_prompt(
    message: Message, user: User, session: AsyncSession, state: FSMContext
) -> None:
    if not message.text:
        return
    user.custom_system_prompt = message.text.strip()[:4000]
    await session.flush()
    await state.clear()
    await message.answer(
        i18n.t("style.saved", locale=user.locale),
        reply_markup=main_menu_kb(user.locale),
    )


@router.callback_query(F.data == "style:analyze")
async def cb_analyze(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    sub = await ensure_subscription(session, user)
    if not sub.features.can_analyze_channel_style:
        await callback.answer(
            i18n.t("style.style_analyze_premium_only", locale=user.locale),
            show_alert=True,
        )
        return
    result = await session.execute(
        select(Channel).where(Channel.user_id == user.id).order_by(Channel.id).limit(1)
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        await callback.answer(i18n.t("channels.empty", locale=user.locale), show_alert=True)
        return
    handle = f"@{channel.username}" if channel.username else str(channel.telegram_chat_id)
    style = await analyze_channel_style(handle)
    if style is None:
        await callback.answer(i18n.t("errors.generic", locale=user.locale), show_alert=True)
        return
    channel.style_summary = style
    await session.flush()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("style.style_analyzed", locale=user.locale),
            reply_markup=main_menu_kb(user.locale),
        )
    await callback.answer()
