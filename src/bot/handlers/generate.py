"""Generate-post FSM flow."""

from __future__ import annotations

from datetime import UTC, datetime

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.bot.keyboards import confirm_publish_kb, main_menu_kb, period_kb
from src.bot.keyboards.menu import channel_pick_kb, topic_kb
from src.bot.states import GeneratePost
from src.core.i18n import i18n
from src.core.logging import get_logger
from src.models import (
    Channel,
    Post,
    PostStatus,
    PublishMode,
    Source,
    User,
)
from src.services.collectors.base import Period
from src.services.promo import maybe_post_in_channel_promo
from src.services.publisher import GenerateRequest, generate_post, publish_post
from src.services.subscription import ensure_subscription, increment_post_counter
from src.services.watermark import apply_watermark

logger = get_logger(__name__)
router = Router(name="generate")


@router.callback_query(F.data == "menu:generate")
async def cb_menu_generate(
    callback: CallbackQuery, user: User, session: AsyncSession, state: FSMContext
) -> None:
    sub = await ensure_subscription(session, user)
    if sub.remaining_posts() <= 0:
        await callback.answer(
            i18n.t(
                "generate.limit_reached",
                locale=user.locale,
                tier=sub.tier.value,
                limit=sub.features.monthly_post_limit,
            ),
            show_alert=True,
        )
        return

    channels = await _list_channels(session, user)
    if not channels:
        await callback.answer(i18n.t("channels.empty", locale=user.locale), show_alert=True)
        return
    # Sources are optional: web search runs implicitly from the post topic,
    # so the user can generate posts even without configuring any RSS/TG sources.

    await state.set_state(GeneratePost.choose_channel)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("generate.choose_channel", locale=user.locale),
            reply_markup=channel_pick_kb(user.locale, channels),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("gen:channel:"), GeneratePost.choose_channel)
async def cb_choose_channel(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    channel_id = int(parts[2])
    await state.update_data(channel_id=channel_id)
    await state.set_state(GeneratePost.choose_period)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("generate.choose_period", locale=user.locale),
            reply_markup=period_kb(user.locale),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("gen:period:"), GeneratePost.choose_period)
async def cb_choose_period(callback: CallbackQuery, user: User, state: FSMContext) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    period = parts[2]
    if period not in {"hour", "day", "week", "month"}:
        await callback.answer()
        return
    await state.update_data(period=period)
    await state.set_state(GeneratePost.enter_topic)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            i18n.t("generate.topic_prompt", locale=user.locale),
            parse_mode="HTML",
            reply_markup=topic_kb(user.locale),
        )
    await callback.answer()


@router.message(GeneratePost.enter_topic)
async def msg_topic(message: Message, user: User, session: AsyncSession, state: FSMContext) -> None:
    topic = (message.text or "").strip() or None
    await _kickoff_generation(message, user, session, state, topic=topic)


@router.callback_query(GeneratePost.enter_topic, F.data == "generate:topic_skip")
async def cb_topic_skip(
    callback: CallbackQuery, user: User, session: AsyncSession, state: FSMContext
) -> None:
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    await callback.answer()
    await _kickoff_generation(callback.message, user, session, state, topic=None)


async def _kickoff_generation(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    *,
    topic: str | None,
) -> None:
    data = await state.get_data()
    channel_id = data.get("channel_id")
    period = data.get("period", "day")
    if channel_id is None:
        await state.clear()
        await message.answer(i18n.t("errors.generic", locale=user.locale))
        return

    channel = (
        await session.execute(
            select(Channel).where(Channel.id == channel_id, Channel.user_id == user.id)
        )
    ).scalar_one_or_none()
    if channel is None:
        await state.clear()
        await message.answer(i18n.t("errors.generic", locale=user.locale))
        return

    sources = await _list_sources(session, user)
    sub = await ensure_subscription(session, user)
    feat = sub.features

    progress = await message.answer(i18n.t("generate.collecting", locale=user.locale))

    req = GenerateRequest(
        user_id=user.id,
        topic=topic,
        period=period,
        sources=sources,
        locale=user.locale,
        tier=sub.tier,
        custom_system_prompt=user.custom_system_prompt if feat.can_use_custom_prompt else None,
        channel_style=channel.style_summary if feat.can_analyze_channel_style else None,
        want_image=feat.can_generate_images or _has_stock_keys(),
    )

    try:
        await progress.edit_text(i18n.t("generate.writing", locale=user.locale))
        result = await generate_post(req)
    except Exception as exc:
        logger.warning("generate.failed", error=str(exc))
        await progress.edit_text(
            i18n.t("generate.failed", locale=user.locale, error=str(exc)),
        )
        await state.clear()
        return

    body_text = result.body_text
    bot = message.bot
    assert bot is not None

    if feat.has_watermark:
        me = await bot.get_me()
        signature = i18n.t(
            "watermark.signature",
            locale=user.locale,
            bot_username=me.username or "",
        )
        # marker value: low 16 bits of user id (post id not yet known)
        body_text = apply_watermark(body_text, signature=signature, marker_value=user.id & 0xFFFF)

    post = Post(
        user_id=user.id,
        channel_id=channel.id,
        status=PostStatus.DRAFT,
        topic=topic,
        body_text=body_text,
        image_url=result.image.url if result.image else None,
        image_source=result.image.source if result.image else None,
        has_watermark=feat.has_watermark,
    )
    session.add(post)
    await session.flush()

    await state.update_data(post_id=post.id)

    if user.publish_mode == PublishMode.AUTO:
        await _publish_and_finalize(message, bot, user, session, post)
        await progress.delete()
        return

    await state.set_state(GeneratePost.confirm)
    preview_text = body_text + "\n\n" + i18n.t("generate.preview_caption", locale=user.locale)
    await progress.delete()
    if result.image is not None:
        try:
            await message.answer_photo(result.image.url, caption=preview_text[:1024])
        except Exception:
            await message.answer(preview_text, parse_mode="HTML")
    else:
        await message.answer(preview_text, parse_mode="HTML")
    await message.answer(
        i18n.t("generate.preview_caption", locale=user.locale),
        reply_markup=confirm_publish_kb(user.locale),
    )


@router.callback_query(F.data == "gen:publish", GeneratePost.confirm)
async def cb_publish(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    post_id = data.get("post_id")
    if post_id is None:
        await callback.answer()
        return
    post = (
        await session.execute(
            select(Post)
            .options(selectinload(Post.channel))
            .where(Post.id == post_id, Post.user_id == user.id)
        )
    ).scalar_one_or_none()
    if post is None:
        await callback.answer()
        return

    bot = callback.bot
    assert bot is not None
    if isinstance(callback.message, Message):
        await _publish_and_finalize(callback.message, bot, user, session, post)
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "gen:regenerate", GeneratePost.confirm)
async def cb_regenerate(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    if "post_id" in data:
        post = (
            await session.execute(
                select(Post).where(Post.id == data["post_id"], Post.user_id == user.id)
            )
        ).scalar_one_or_none()
        if post is not None:
            await session.delete(post)
            await session.flush()

    await state.set_state(GeneratePost.enter_topic)
    if isinstance(callback.message, Message):
        await callback.message.answer(
            i18n.t("generate.topic_prompt", locale=user.locale),
            parse_mode="HTML",
            reply_markup=topic_kb(user.locale),
        )
    await callback.answer()


async def _publish_and_finalize(
    notify_target: Message,
    bot: Bot,
    user: User,
    session: AsyncSession,
    post: Post,
) -> None:
    if post.channel is None:
        return
    try:
        published = await publish_post(
            bot,
            chat_id=post.channel.telegram_chat_id,
            text=post.body_text,
            image_url=post.image_url,
        )
    except Exception as exc:
        logger.warning("publish.failed", post_id=post.id, error=str(exc))
        post.status = PostStatus.FAILED
        await session.flush()
        await notify_target.answer(i18n.t("generate.failed", locale=user.locale, error=str(exc)))
        return

    post.status = PostStatus.PUBLISHED
    post.telegram_message_id = published.message_id
    post.published_at = datetime.now(UTC)
    await increment_post_counter(session, user)
    await session.flush()

    sub = await ensure_subscription(session, user)
    await maybe_post_in_channel_promo(
        bot,
        chat_id=post.channel.telegram_chat_id,
        locale=user.locale,
        subscription=sub,
    )

    await notify_target.answer(
        i18n.t("generate.published", locale=user.locale),
        reply_markup=main_menu_kb(user.locale),
    )


def _has_stock_keys() -> bool:
    from src.core.config import settings

    return bool(
        (settings.unsplash_access_key and settings.unsplash_access_key.get_secret_value())
        or (settings.pexels_api_key and settings.pexels_api_key.get_secret_value())
    )


async def _list_channels(session: AsyncSession, user: User) -> list[Channel]:
    result = await session.execute(
        select(Channel).where(Channel.user_id == user.id).order_by(Channel.id)
    )
    return list(result.scalars().all())


async def _list_sources(session: AsyncSession, user: User) -> list[Source]:
    result = await session.execute(
        select(Source).where(Source.user_id == user.id).order_by(Source.id)
    )
    return list(result.scalars().all())


# unused, but lets us keep Period import without flake noise
_ = Period
