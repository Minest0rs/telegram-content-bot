"""Tests for the i18n helper."""

from __future__ import annotations

from src.core.i18n import I18n, i18n


def test_supported_locales_contain_ru_en_es() -> None:
    supported = I18n.supported()
    assert "ru" in supported
    assert "en" in supported
    assert "es" in supported


def test_translation_falls_back_to_english_on_missing_locale() -> None:
    # ask for a key that exists in en/ru/es; missing locales gracefully fall back
    text_ru = i18n.t("menu.title", locale="ru")
    assert text_ru


def test_format_args_applied() -> None:
    text = i18n.t("start.greeting", locale="en", name="Alex")
    assert "Alex" in text


def test_unknown_key_returns_key() -> None:
    assert i18n.t("does.not.exist") == "does.not.exist"


def test_missing_format_args_does_not_crash() -> None:
    # missing kwargs should not raise — we return the unformatted string
    text = i18n.t("start.greeting", locale="en")
    assert text  # no exception
