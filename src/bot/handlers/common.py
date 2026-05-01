"""/start, /menu, language switch, generic callbacks."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import language_kb, main_menu_kb
from src.core.i18n import I18n, i18n
from src.models import User

router = Router(name="common")


@router.message(CommandStart())
async def on_start(message: Message, user: User, state: FSMContext) -> None:
    await state.clear()
    name = user.first_name or user.username or "👋"
    text = i18n.t("start.greeting", locale=user.locale, name=name)
    await message.answer(text, reply_markup=main_menu_kb(user.locale), parse_mode="HTML")


@router.message(Command("menu"))
async def on_menu(message: Message, user: User, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        i18n.t("menu.title", locale=user.locale),
        reply_markup=main_menu_kb(user.locale),
    )


@router.callback_query(F.data == "menu:main")
async def cb_menu_main(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.clear()
    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(
                i18n.t("menu.title", locale=user.locale),
                reply_markup=main_menu_kb(user.locale),
            )
        except Exception:
            await callback.message.answer(
                i18n.t("menu.title", locale=user.locale),
                reply_markup=main_menu_kb(user.locale),
            )
    await callback.answer()


@router.callback_query(F.data == "menu:language")
async def cb_menu_language(callback: CallbackQuery, user: User) -> None:
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("language.choose", locale=user.locale), reply_markup=language_kb()
        )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def cb_set_language(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    code = (callback.data or "").split(":", 1)[1]
    if code not in I18n.supported():
        await callback.answer("?")
        return
    user.locale = code
    await session.flush()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("language.changed", locale=code) + "\n\n" + i18n.t("menu.title", locale=code),
            reply_markup=main_menu_kb(code),
        )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def cb_help(callback: CallbackQuery, user: User) -> None:
    text = (
        "<b>How to use this bot:</b>\n\n"
        "1. Add a Telegram channel where I'll publish (you must add me as admin).\n"
        "2. Configure information sources — web search queries, RSS feeds, or other channels to mimic.\n"
        "3. Tap «Create post» whenever you want fresh content.\n\n"
        "On the Free tier you get 3 posts per month with a small watermark and "
        "an occasional bot-promo message in your channel.\n\n"
        "Upgrade to Pro for image generation and 50 posts/mo, or Premium for "
        "unlimited posts, custom system prompts and channel-style mimicry."
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text, reply_markup=main_menu_kb(user.locale), parse_mode="HTML"
        )
    await callback.answer()


@router.message(Command("publish_mode"))
async def cmd_publish_mode(message: Message, user: User) -> None:
    from src.bot.keyboards import publish_mode_kb

    await message.answer(
        i18n.t("publish.mode_title", locale=user.locale),
        reply_markup=publish_mode_kb(user.locale),
    )


@router.callback_query(F.data.startswith("mode:"))
async def cb_publish_mode(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    from src.models import PublishMode

    mode = (callback.data or "").split(":", 1)[1]
    user.publish_mode = PublishMode(mode)
    await session.flush()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("publish.mode_set", locale=user.locale),
            reply_markup=main_menu_kb(user.locale),
        )
    await callback.answer()
