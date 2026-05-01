"""Choose an AI provider based on config."""

from __future__ import annotations

from src.core.config import AIProvider as ProviderName
from src.core.config import settings
from src.core.logging import get_logger
from src.services.ai.base import AIProvider, AIProviderError, ChatMessage
from src.services.ai.gemini import GeminiProvider
from src.services.ai.groq import GroqProvider
from src.services.ai.openai_provider import OpenAIProvider

logger = get_logger(__name__)

_REGISTRY: dict[ProviderName, type[AIProvider]] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "openai": OpenAIProvider,
    # claude is paid; not implemented here, but easy to add
}

_singletons: dict[ProviderName, AIProvider] = {}


def _candidates(name: ProviderName | None = None) -> list[ProviderName]:
    candidates: list[ProviderName] = []
    if name is not None:
        candidates.append(name)
    if settings.ai_provider not in candidates:
        candidates.append(settings.ai_provider)
    fallbacks: tuple[ProviderName, ...] = ("gemini", "groq", "openai")
    for fallback in fallbacks:
        if fallback not in candidates:
            candidates.append(fallback)
    return candidates


def _instantiate(cand: ProviderName) -> AIProvider:
    if cand not in _singletons:
        _singletons[cand] = _REGISTRY[cand]()
    return _singletons[cand]


def get_provider(name: ProviderName | None = None) -> AIProvider:
    """Return the first configured AI provider, preferring ``name`` / settings."""
    last_error: str | None = None
    for cand in _candidates(name):
        if cand not in _REGISTRY:
            continue
        provider = _instantiate(cand)
        if provider.is_configured():
            return provider
        last_error = f"{cand} not configured"
    raise AIProviderError(f"No AI provider is configured ({last_error})")


async def complete_with_fallback(
    messages: list[ChatMessage],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1200,
    name: ProviderName | None = None,
) -> str:
    """Run completion through the preferred provider; on failure (quota,
    network, etc.) fall through to the next configured one.

    This is the recommended entry point for any post-generation call that
    should not abort the user's flow on a single provider hiccup.
    """
    last_error: Exception | None = None
    for cand in _candidates(name):
        if cand not in _REGISTRY:
            continue
        provider = _instantiate(cand)
        if not provider.is_configured():
            continue
        try:
            return await provider.complete(messages, temperature=temperature, max_tokens=max_tokens)
        except AIProviderError as exc:
            logger.warning("ai.provider_failed", provider=cand, error=str(exc))
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise AIProviderError("No AI provider is configured")
