"""Manage user channels."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import channels_kb, main_menu_kb
from src.bot.states import AddChannel
from src.core.i18n import i18n
from src.core.logging import get_logger
from src.models import Channel, User

logger = get_logger(__name__)
router = Router(name="channels")


@router.callback_query(F.data == "menu:channels")
async def cb_menu_channels(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    channels = await _list_channels(session, user)
    text = (
        i18n.t("channels.list_title", locale=user.locale)
        if channels
        else i18n.t("channels.empty", locale=user.locale)
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=channels_kb(user.locale, channels))
    await callback.answer()


@router.callback_query(F.data == "channel:add")
async def cb_channel_add(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.set_state(AddChannel.waiting_for_channel)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("channels.add_prompt", locale=user.locale), parse_mode="HTML"
        )
    await callback.answer()


@router.message(AddChannel.waiting_for_channel)
async def msg_add_channel(
    message: Message, user: User, session: AsyncSession, state: FSMContext
) -> None:
    chat_id: int | None = None
    title: str | None = None
    username: str | None = None

    if message.forward_from_chat is not None:
        chat = message.forward_from_chat
        chat_id = chat.id
        title = chat.title or chat.full_name or str(chat.id)
        username = chat.username
    elif message.text:
        text = message.text.strip()
        if text.startswith("@"):
            username = text.removeprefix("@")
            try:
                chat = await message.bot.get_chat(text)  # type: ignore[union-attr]
                chat_id = chat.id
                title = chat.title or text
                username = chat.username or username
            except Exception as exc:
                logger.warning("channel.resolve_failed", value=text, error=str(exc))
                await message.answer(i18n.t("errors.generic", locale=user.locale))
                return

    if chat_id is None or title is None:
        await message.answer(i18n.t("channels.add_prompt", locale=user.locale), parse_mode="HTML")
        return

    # check that the bot is admin
    me = await message.bot.get_me()  # type: ignore[union-attr]
    try:
        member = await message.bot.get_chat_member(chat_id, me.id)  # type: ignore[union-attr]
        if member.status not in {"administrator", "creator"}:
            await message.answer(i18n.t("channels.not_admin", locale=user.locale))
            return
    except Exception as exc:
        logger.warning("channel.member_check_failed", chat_id=chat_id, error=str(exc))
        await message.answer(i18n.t("channels.not_admin", locale=user.locale))
        return

    existing = await session.execute(
        select(Channel).where(Channel.user_id == user.id, Channel.telegram_chat_id == chat_id)
    )
    channel = existing.scalar_one_or_none()
    if channel is None:
        channel = Channel(
            user_id=user.id,
            telegram_chat_id=chat_id,
            title=title,
            username=username,
        )
        session.add(channel)
    else:
        channel.title = title
        channel.username = username
    await session.flush()

    await state.clear()
    await message.answer(
        i18n.t("channels.added", locale=user.locale, title=title),
        reply_markup=main_menu_kb(user.locale),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("channel:remove:"))
async def cb_channel_remove(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    channel_id = int(parts[2])
    result = await session.execute(
        select(Channel).where(Channel.id == channel_id, Channel.user_id == user.id)
    )
    channel = result.scalar_one_or_none()
    if channel is not None:
        await session.delete(channel)
        await session.flush()

    channels = await _list_channels(session, user)
    text = (
        i18n.t("channels.list_title", locale=user.locale)
        if channels
        else i18n.t("channels.empty", locale=user.locale)
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=channels_kb(user.locale, channels))
    await callback.answer(i18n.t("channels.removed", locale=user.locale))


async def _list_channels(session: AsyncSession, user: User) -> list[Channel]:
    result = await session.execute(
        select(Channel).where(Channel.user_id == user.id).order_by(Channel.id)
    )
    return list(result.scalars().all())
