"""Choose an AI provider based on config."""

from __future__ import annotations

from src.core.config import AIProvider as ProviderName
from src.core.config import settings
from src.services.ai.base import AIProvider, AIProviderError
from src.services.ai.gemini import GeminiProvider
from src.services.ai.groq import GroqProvider
from src.services.ai.openai_provider import OpenAIProvider

_REGISTRY: dict[ProviderName, type[AIProvider]] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "openai": OpenAIProvider,
    # claude is paid; not implemented here, but easy to add
}

_singletons: dict[ProviderName, AIProvider] = {}


def get_provider(name: ProviderName | None = None) -> AIProvider:
    """Return a configured AI provider; falls back to any working one."""
    candidates: list[ProviderName] = []
    if name is not None:
        candidates.append(name)
    candidates.append(settings.ai_provider)
    fallbacks: tuple[ProviderName, ...] = ("gemini", "groq", "openai")
    for fallback in fallbacks:
        if fallback not in candidates:
            candidates.append(fallback)

    last_error: str | None = None
    for cand in candidates:
        if cand not in _REGISTRY:
            continue
        if cand not in _singletons:
            _singletons[cand] = _REGISTRY[cand]()
        provider = _singletons[cand]
        if provider.is_configured():
            return provider
        last_error = f"{cand} not configured"

    raise AIProviderError(f"No AI provider is configured ({last_error})")
