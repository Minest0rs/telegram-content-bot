"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AIProvider = Literal["gemini", "groq", "openai", "claude"]
Locale = Literal["ru", "en", "es"]


class Settings(BaseSettings):
    """Application settings.

    All values come from environment variables (or a .env file in dev).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="before")
    @classmethod
    def _empty_strings_to_none(cls, data: object) -> object:
        """Treat empty .env values (`KEY=`) as ``None`` for optional fields."""
        if not isinstance(data, dict):
            return data
        return {k: (None if isinstance(v, str) and v.strip() == "" else v) for k, v in data.items()}

    # --- Telegram bot ---
    bot_token: SecretStr = Field(default=SecretStr(""))
    bot_owner_id: int | None = None
    bot_showcase_channel: str | None = None

    # --- Telethon (channel parsing) ---
    telegram_api_id: int | None = None
    telegram_api_hash: SecretStr | None = None
    telegram_session_name: str = "content_bot"

    # --- AI ---
    ai_provider: AIProvider = "gemini"

    gemini_api_key: SecretStr | None = None
    gemini_model_basic: str = "gemini-2.0-flash"
    gemini_model_premium: str = "gemini-2.5-pro"

    groq_api_key: SecretStr | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    openai_api_key: SecretStr | None = None
    openai_model_basic: str = "gpt-4o-mini"
    openai_model_premium: str = "gpt-4o"

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"

    # --- Image sources ---
    unsplash_access_key: SecretStr | None = None
    pexels_api_key: SecretStr | None = None

    # --- Database & queue ---
    database_url: str = "postgresql+asyncpg://content_bot:content_bot@localhost:5432/content_bot"
    redis_url: str = "redis://localhost:6379/0"

    # --- App ---
    default_locale: Locale = "ru"
    watermark_scan_interval: int = 3600  # 1 hour
    log_level: str = "INFO"

    @property
    def has_gemini(self) -> bool:
        return self.gemini_api_key is not None and bool(self.gemini_api_key.get_secret_value())

    @property
    def has_groq(self) -> bool:
        return self.groq_api_key is not None and bool(self.groq_api_key.get_secret_value())

    @property
    def has_openai(self) -> bool:
        return self.openai_api_key is not None and bool(self.openai_api_key.get_secret_value())

    @property
    def has_anthropic(self) -> bool:
        return self.anthropic_api_key is not None and bool(
            self.anthropic_api_key.get_secret_value()
        )

    @property
    def has_telethon(self) -> bool:
        return (
            self.telegram_api_id is not None
            and self.telegram_api_hash is not None
            and bool(self.telegram_api_hash.get_secret_value())
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
