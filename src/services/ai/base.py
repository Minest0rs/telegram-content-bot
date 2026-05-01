"""Abstract base for AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


class AIProviderError(RuntimeError):
    """Raised when an AI provider call fails."""


class AIProvider(ABC):
    """Common interface for text-completion AI backends."""

    name: str = "abstract"

    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Run a chat completion and return the assistant's text."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the provider has the necessary credentials."""
