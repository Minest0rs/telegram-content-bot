"""Publish a generated post to a Telegram channel via the bot."""

from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PublishedMessage:
    chat_id: int
    message_id: int


async def publish_post(
    bot: Bot,
    *,
    chat_id: int,
    text: str,
    image_url: str | None = None,
) -> PublishedMessage:
    """Send the text (with optional photo) to the channel.

    Telegram caption limit is 1024 chars; if text is longer with an image, we
    fall back to sending the photo first then the text as a separate message.
    """
    parse_mode = "HTML"

    if image_url and len(text) <= 1024:
        try:
            msg = await bot.send_photo(
                chat_id=chat_id, photo=image_url, caption=text, parse_mode=parse_mode
            )
            return PublishedMessage(chat_id=msg.chat.id, message_id=msg.message_id)
        except TelegramBadRequest as exc:
            logger.warning("publish.send_photo_failed", error=str(exc))

    if image_url:
        try:
            await bot.send_photo(chat_id=chat_id, photo=image_url)
        except TelegramBadRequest as exc:
            logger.warning("publish.image_failed", error=str(exc))

    msg = await bot.send_message(
        chat_id=chat_id, text=text, parse_mode=parse_mode, disable_web_page_preview=False
    )
    return PublishedMessage(chat_id=msg.chat.id, message_id=msg.message_id)
