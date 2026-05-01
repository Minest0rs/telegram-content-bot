"""Google Gemini provider via google-genai."""

from __future__ import annotations

import asyncio
from typing import Any

from src.core.config import settings
from src.core.logging import get_logger
from src.services.ai.base import AIProvider, AIProviderError, ChatMessage

logger = get_logger(__name__)


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self) -> None:
        self._client: Any | None = None

    def is_configured(self) -> bool:
        return settings.has_gemini

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self.is_configured():
            raise AIProviderError("GEMINI_API_KEY is not set")
        try:
            from google import genai
        except ImportError as exc:  # pragma: no cover
            raise AIProviderError("google-genai is not installed") from exc

        assert settings.gemini_api_key is not None
        self._client = genai.Client(api_key=settings.gemini_api_key.get_secret_value())
        return self._client

    @staticmethod
    def _to_gemini_contents(messages: list[ChatMessage]) -> tuple[str | None, list[dict[str, Any]]]:
        """Split off system message, convert the rest to gemini's role/parts format."""
        system_text: str | None = None
        contents: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == "system":
                system_text = f"{system_text}\n\n{msg.content}" if system_text else msg.content
                continue
            role = "user" if msg.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})
        return system_text, contents

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        client = self._get_client()
        model_name = model or settings.gemini_model_basic
        system_text, contents = self._to_gemini_contents(messages)

        from google.genai import types as genai_types

        config = genai_types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_text,
        )

        def _call() -> str:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            text = getattr(response, "text", None)
            if not text:
                raise AIProviderError("Gemini returned empty response")
            return str(text).strip()

        try:
            return await asyncio.to_thread(_call)
        except AIProviderError:
            raise
        except Exception as exc:
            logger.error("gemini.complete_failed", error=str(exc))
            raise AIProviderError(f"Gemini error: {exc}") from exc
