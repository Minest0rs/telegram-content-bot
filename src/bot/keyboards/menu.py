"""Inline keyboards for the bot UI."""

from __future__ import annotations

from collections.abc import Iterable

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.i18n import i18n
from src.models import Channel, Source


def main_menu_kb(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.generate", locale=locale), callback_data="menu:generate"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.channels", locale=locale), callback_data="menu:channels"
                ),
                InlineKeyboardButton(
                    text=i18n.t("menu.sources", locale=locale), callback_data="menu:sources"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.style", locale=locale), callback_data="menu:style"
                ),
                InlineKeyboardButton(
                    text=i18n.t("menu.subscription", locale=locale),
                    callback_data="menu:subscription",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.language", locale=locale), callback_data="menu:language"
                ),
                InlineKeyboardButton(
                    text=i18n.t("menu.help", locale=locale), callback_data="menu:help"
                ),
            ],
        ]
    )


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
                InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang:es"),
            ],
            [InlineKeyboardButton(text="←", callback_data="menu:main")],
        ]
    )


def subscription_kb(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t("subscription.buy_pro", locale=locale), callback_data="sub:buy:pro"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("subscription.buy_premium", locale=locale),
                    callback_data="sub:buy:premium",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.back", locale=locale), callback_data="menu:main"
                )
            ],
        ]
    )


def channels_kb(locale: str, channels: Iterable[Channel]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for ch in channels:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"📢 {ch.display_name}", callback_data=f"channel:view:{ch.id}"
                ),
                InlineKeyboardButton(text="🗑", callback_data=f"channel:remove:{ch.id}"),
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=i18n.t("channels.add", locale=locale), callback_data="channel:add"
            )
        ]
    )
    rows.append(
        [InlineKeyboardButton(text=i18n.t("menu.back", locale=locale), callback_data="menu:main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def sources_kb(
    locale: str,
    sources: Iterable[Source],
    *,
    show_telegram: bool = True,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for src in sources:
        emoji = {"web": "🔍", "rss": "📡", "telegram": "📨"}[src.type.value]
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{emoji} {src.value[:40]}", callback_data=f"source:view:{src.id}"
                ),
                InlineKeyboardButton(text="🗑", callback_data=f"source:remove:{src.id}"),
            ]
        )
    # Web is implicit (auto-runs from the post topic), so we don't expose
    # it as an addable source kind to keep the menu non-confusing.
    add_row = [
        InlineKeyboardButton(
            text=i18n.t("sources.rss", locale=locale), callback_data="source:add:rss"
        ),
    ]
    if show_telegram:
        add_row.append(
            InlineKeyboardButton(
                text=i18n.t("sources.telegram", locale=locale),
                callback_data="source:add:telegram",
            ),
        )
    rows.append(add_row)
    rows.append(
        [InlineKeyboardButton(text=i18n.t("menu.back", locale=locale), callback_data="menu:main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_kb(locale: str) -> InlineKeyboardMarkup:
    """Single-button keyboard to abort an FSM step."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.cancel", locale=locale),
                    callback_data="fsm:cancel",
                )
            ]
        ]
    )


def topic_kb(locale: str) -> InlineKeyboardMarkup:
    """Skip + Cancel buttons for the topic-entry step."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t("generate.topic_skip", locale=locale),
                    callback_data="generate:topic_skip",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.cancel", locale=locale),
                    callback_data="fsm:cancel",
                )
            ],
        ]
    )


def style_kb(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t("style.system_prompt", locale=locale),
                    callback_data="style:edit_prompt",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("style.style_analyze", locale=locale),
                    callback_data="style:analyze",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.back", locale=locale), callback_data="menu:main"
                )
            ],
        ]
    )


def period_kb(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t("generate.period.hour", locale=locale),
                    callback_data="gen:period:hour",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("generate.period.day", locale=locale),
                    callback_data="gen:period:day",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("generate.period.week", locale=locale),
                    callback_data="gen:period:week",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("generate.period.month", locale=locale),
                    callback_data="gen:period:month",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.cancel", locale=locale), callback_data="menu:main"
                )
            ],
        ]
    )


def confirm_publish_kb(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t("generate.publish", locale=locale), callback_data="gen:publish"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("generate.regenerate", locale=locale),
                    callback_data="gen:regenerate",
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("generate.cancel", locale=locale), callback_data="menu:main"
                )
            ],
        ]
    )


def publish_mode_kb(locale: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=i18n.t("publish.mode_auto", locale=locale), callback_data="mode:auto"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("publish.mode_preview", locale=locale), callback_data="mode:preview"
                )
            ],
            [
                InlineKeyboardButton(
                    text=i18n.t("menu.back", locale=locale), callback_data="menu:main"
                )
            ],
        ]
    )


def channel_pick_kb(locale: str, channels: Iterable[Channel]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"📢 {ch.display_name}", callback_data=f"gen:channel:{ch.id}")]
        for ch in channels
    ]
    rows.append(
        [InlineKeyboardButton(text=i18n.t("menu.cancel", locale=locale), callback_data="menu:main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
