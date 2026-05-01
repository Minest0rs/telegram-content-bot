"""OpenAI provider (uses the Chat Completions endpoint via raw HTTP)."""

from __future__ import annotations

from typing import Any

import httpx

from src.core.config import settings
from src.core.logging import get_logger
from src.services.ai.base import AIProvider, AIProviderError, ChatMessage

logger = get_logger(__name__)

OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIProvider(AIProvider):
    name = "openai"

    def is_configured(self) -> bool:
        return settings.has_openai

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        if not self.is_configured():
            raise AIProviderError("OPENAI_API_KEY is not set")
        assert settings.openai_api_key is not None

        payload: dict[str, Any] = {
            "model": model or settings.openai_model_basic,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{OPENAI_BASE_URL}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if not content:
                    raise AIProviderError("OpenAI returned empty response")
                return str(content).strip()
        except httpx.HTTPStatusError as exc:
            logger.error("openai.http_error", status=exc.response.status_code)
            raise AIProviderError(
                f"OpenAI HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            logger.error("openai.complete_failed", error=str(exc))
            raise AIProviderError(f"OpenAI error: {exc}") from exc
