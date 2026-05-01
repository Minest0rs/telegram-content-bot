"""Manage information sources for posts."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import main_menu_kb, sources_kb
from src.bot.states import AddSource
from src.core.i18n import i18n
from src.models import Source, SourceType, User
from src.services.collectors import collect_rss

router = Router(name="sources")


@router.callback_query(F.data == "menu:sources")
async def cb_menu_sources(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    sources = await _list_sources(session, user)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("sources.title", locale=user.locale),
            reply_markup=sources_kb(user.locale, sources),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("source:add:"))
async def cb_source_add(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    kind = parts[2] if len(parts) > 2 else "web"
    await state.set_state(AddSource.waiting_for_value)
    await state.update_data(kind=kind)
    prompt_key = {
        "web": "sources.web",
        "rss": "sources.add_rss_prompt",
        "telegram": "sources.add_tg_prompt",
    }.get(kind, "sources.title")
    if kind == "web":
        prompt = (
            "Введите ключевые слова или поисковый запрос.\n"
            "Например: <code>искусственный интеллект</code>"
            if user.locale == "ru"
            else "Enter keywords or a search query.\ne.g. <code>artificial intelligence</code>"
        )
    else:
        prompt = i18n.t(prompt_key, locale=user.locale)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(prompt, parse_mode="HTML")
    await callback.answer()


@router.message(AddSource.waiting_for_value)
async def msg_add_source(
    message: Message, user: User, session: AsyncSession, state: FSMContext
) -> None:
    if not message.text:
        return
    data = await state.get_data()
    kind = data.get("kind", "web")
    value = message.text.strip()

    if kind == "rss":
        # quick sanity check that we can read it
        items = await collect_rss(value, period="month", max_results=1)
        if not items:
            await message.answer(i18n.t("sources.invalid_rss", locale=user.locale))
            return

    src = Source(user_id=user.id, type=SourceType(kind), value=value, enabled=True)
    session.add(src)
    await session.flush()

    await state.clear()
    sources = await _list_sources(session, user)
    await message.answer(
        i18n.t("sources.added", locale=user.locale),
        reply_markup=sources_kb(user.locale, sources),
    )


@router.callback_query(F.data.startswith("source:remove:"))
async def cb_source_remove(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    src_id = int(parts[2])
    result = await session.execute(
        select(Source).where(Source.id == src_id, Source.user_id == user.id)
    )
    src = result.scalar_one_or_none()
    if src is not None:
        await session.delete(src)
        await session.flush()

    sources = await _list_sources(session, user)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("sources.title", locale=user.locale),
            reply_markup=sources_kb(user.locale, sources),
        )
    await callback.answer(i18n.t("sources.removed", locale=user.locale))


@router.callback_query(F.data.startswith("source:view:"))
async def cb_source_view(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    src_id = int(parts[2])
    result = await session.execute(
        select(Source).where(Source.id == src_id, Source.user_id == user.id)
    )
    src = result.scalar_one_or_none()
    if src is None:
        await callback.answer()
        return
    text = f"<b>{src.type.value}</b>\n<code>{src.value}</code>"
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text, reply_markup=main_menu_kb(user.locale), parse_mode="HTML"
        )
    await callback.answer()


async def _list_sources(session: AsyncSession, user: User) -> list[Source]:
    result = await session.execute(
        select(Source).where(Source.user_id == user.id).order_by(Source.id)
    )
    return list(result.scalars().all())
