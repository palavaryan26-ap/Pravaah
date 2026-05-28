"""Abstract AI provider and concrete implementations.

The provider layer abstracts away the specifics of each AI service
(OpenAI, Anthropic, local models, etc.) behind a common interface.

Architecture Notes:
    - ``AIProvider`` is the abstract base.  Every concrete provider must
      implement ``complete()`` and optionally ``embed()``.
    - ``OpenAIProvider`` wraps the ``openai`` async client.
    - ``MockProvider`` returns deterministic responses for testing and
      development without API keys.
    - Provider selection is driven by ``AIConfig.provider`` and resolved
      at startup by ``create_provider()``.

Scalability:
    - Adding a new provider (e.g. Anthropic, Ollama, Gemini) is a single
      class that implements ``complete()`` — no other code changes.
    - The ``AIMessage`` / ``AIResponse`` data models keep the interface
      provider-agnostic so consumers never depend on SDK specifics.
"""
from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("pravaah.ai.provider")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class AIMessage:
    """A single message in a conversation.

    Attributes:
        role: The message role (``"system"``, ``"user"``, ``"assistant"``).
        content: The text content.
    """

    role: str
    content: str


@dataclass
class AIResponse:
    """Response from an AI provider.

    Attributes:
        content: The generated text.
        model: The model that produced the response.
        usage: Token usage metadata (provider-specific).
        raw: The raw provider response for debugging.
    """

    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class AIProvider(abc.ABC):
    """Abstract AI provider interface.

    Every concrete provider must implement at least ``complete()``.
    """

    @abc.abstractmethod
    async def complete(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Generate a completion from a list of messages.

        Args:
            messages: Conversation history as ``AIMessage`` objects.
            model: Override the default model.
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum tokens to generate.

        Returns:
            An ``AIResponse`` with the generated content.
        """
        ...

    async def embed(self, text: str, *, model: str | None = None) -> list[float]:
        """Generate an embedding vector for text.

        Default implementation raises ``NotImplementedError``.
        Override in providers that support embeddings.

        Args:
            text: The text to embed.
            model: Override the default embedding model.

        Returns:
            A list of floats representing the embedding vector.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support embeddings"
        )


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------


class OpenAIProvider(AIProvider):
    """OpenAI / Azure OpenAI provider.

    Requires the ``openai`` package and a valid API key.

    Args:
        api_key: OpenAI API key.
        default_model: Default model to use (e.g. ``"gpt-4o-mini"``).
        base_url: Optional base URL for Azure or custom endpoints.
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4o-mini",
        base_url: str | None = None,
    ) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "The 'openai' package is required for OpenAIProvider. "
                "Install it with: pip install openai"
            ) from exc

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._default_model = default_model
        logger.info("OpenAI provider initialised (model=%s)", default_model)

    async def complete(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Generate a completion using the OpenAI chat API."""
        target_model = model or self._default_model

        response = await self._client.chat.completions.create(
            model=target_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = {}
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return AIResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=usage,
            raw=response,
        )

    async def embed(self, text: str, *, model: str | None = None) -> list[float]:
        """Generate an embedding using the OpenAI embeddings API."""
        target_model = model or "text-embedding-3-small"

        response = await self._client.embeddings.create(
            model=target_model,
            input=text,
        )
        return response.data[0].embedding


# ---------------------------------------------------------------------------
# Mock provider (for testing / dev without API keys)
# ---------------------------------------------------------------------------


class MockProvider(AIProvider):
    """Mock AI provider for development and testing.

    Returns deterministic, structured responses without making
    any API calls.  Useful for:
      - Running tests without an API key
      - Developing AI-powered features offline
      - CI/CD pipelines
    """

    def __init__(self, default_model: str = "mock-v1") -> None:
        self._default_model = default_model
        logger.info("Mock AI provider initialised (no API calls will be made)")

    async def complete(
        self,
        messages: list[AIMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Return a mock response based on the last user message."""
        last_msg = messages[-1].content if messages else ""
        word_count = len(last_msg.split())

        content = (
            f"[Mock AI Response] Received {len(messages)} message(s), "
            f"last message had {word_count} word(s). "
            f"This is a mock response for development. "
            f"Configure a real AI provider (e.g. OpenAI) in pravaah.yaml "
            f"to get actual AI completions."
        )

        return AIResponse(
            content=content,
            model=model or self._default_model,
            usage={
                "prompt_tokens": word_count * 2,
                "completion_tokens": 30,
                "total_tokens": word_count * 2 + 30,
            },
        )

    async def embed(self, text: str, *, model: str | None = None) -> list[float]:
        """Return a mock embedding vector (128-dimensional)."""
        import hashlib

        # Deterministic but text-dependent mock embedding
        digest = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in digest[:128]]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
    "mock": MockProvider,
}


def create_provider(
    provider_name: str,
    api_key: str = "",
    model: str = "gpt-4o-mini",
    **kwargs: Any,
) -> AIProvider:
    """Create an AI provider instance from config.

    Falls back to ``MockProvider`` if the requested provider requires
    an API key but none is configured.

    Args:
        provider_name: Provider identifier (``"openai"``, ``"mock"``).
        api_key: API key for authenticated providers.
        model: Default model name.
        **kwargs: Additional provider-specific arguments.

    Returns:
        A configured ``AIProvider`` instance.
    """
    if provider_name == "openai" and not api_key:
        logger.warning(
            "OpenAI provider selected but no API key configured. "
            "Falling back to mock provider. Set PRAVAAH_AI__API_KEY "
            "or ai.api_key in pravaah.yaml."
        )
        return MockProvider(default_model=model)

    if provider_name not in _PROVIDERS:
        logger.warning(
            "Unknown AI provider '%s'. Falling back to mock. "
            "Available: %s",
            provider_name,
            list(_PROVIDERS.keys()),
        )
        return MockProvider(default_model=model)

    provider_cls = _PROVIDERS[provider_name]

    if provider_name == "openai":
        return provider_cls(api_key=api_key, default_model=model, **kwargs)

    return provider_cls(default_model=model, **kwargs)
