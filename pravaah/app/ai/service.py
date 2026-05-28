"""High-level AI service with prompt templates.

The ``AIService`` wraps an ``AIProvider`` with domain-specific methods
that encapsulate common AI tasks (summarisation, extraction, classification,
general Q&A).

Architecture Notes:
    - Each method builds a structured prompt from templates, calls the
      provider, and returns a clean result.
    - The service is registered in the ``PravaahRegistry`` as the ``"ai"``
      service so plugins can access it via ``registry.get_service("ai")``.
    - All methods accept optional ``model`` and ``temperature`` overrides
      for per-call tuning.

Scalability:
    - Adding a new AI capability is a single method on this class.
    - Plugins can extend the service by subclassing or wrapping it.
    - The prompt templates are simple f-strings for now; a future
      enhancement could use Jinja2 or a dedicated prompt engine.

Usage::

    ai = registry.get_service("ai")
    summary = await ai.summarize("Long text here...")
    data = await ai.extract("Extract name and email from: ...", schema={"name": "str", "email": "str"})
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from pravaah.app.ai.provider import AIMessage, AIProvider, AIResponse

logger = logging.getLogger("pravaah.ai.service")


@dataclass
class AIServiceConfig:
    """Configuration for the AI service.

    Attributes:
        default_model: Default model for completions.
        default_temperature: Default sampling temperature.
        max_tokens: Default max tokens for completions.
    """

    default_model: str = "gpt-4o-mini"
    default_temperature: float = 0.7
    max_tokens: int = 1024


class AIService:
    """High-level AI service for common tasks.

    Wraps an ``AIProvider`` with domain-specific methods and
    structured prompt templates.

    Args:
        provider: The underlying AI provider.
        config: Service-level configuration.
    """

    def __init__(
        self,
        provider: AIProvider,
        config: AIServiceConfig | None = None,
    ) -> None:
        self._provider = provider
        self._config = config or AIServiceConfig()

    @property
    def provider(self) -> AIProvider:
        """Return the underlying AI provider."""
        return self._provider

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AIResponse:
        """Send a prompt to the AI provider and return the response.

        This is the lowest-level method — all other methods build on it.

        Args:
            prompt: The user prompt.
            system: Optional system message.
            model: Override the default model.
            temperature: Override the default temperature.
            max_tokens: Override the default max tokens.

        Returns:
            The ``AIResponse`` from the provider.
        """
        messages: list[AIMessage] = []
        if system:
            messages.append(AIMessage(role="system", content=system))
        messages.append(AIMessage(role="user", content=prompt))

        return await self._provider.complete(
            messages,
            model=model or self._config.default_model,
            temperature=temperature if temperature is not None else self._config.default_temperature,
            max_tokens=max_tokens or self._config.max_tokens,
        )

    async def summarize(
        self,
        text: str,
        *,
        max_length: int = 200,
        model: str | None = None,
    ) -> str:
        """Summarise a block of text.

        Args:
            text: The text to summarise.
            max_length: Approximate max length of the summary in words.
            model: Override the default model.

        Returns:
            The summary text.
        """
        system = (
            "You are a concise summarisation assistant. "
            f"Produce a summary of at most {max_length} words. "
            "Focus on key points and actionable information."
        )
        response = await self.complete(
            text, system=system, model=model, temperature=0.3,
        )
        logger.debug("Summarised %d chars -> %d chars", len(text), len(response.content))
        return response.content

    async def extract(
        self,
        text: str,
        *,
        schema: dict[str, str],
        model: str | None = None,
    ) -> dict[str, Any]:
        """Extract structured data from unstructured text.

        Args:
            text: The source text.
            schema: A dict mapping field names to descriptions,
                    e.g. ``{"name": "Person's full name", "email": "Email address"}``.
            model: Override the default model.

        Returns:
            A dict with extracted values (best-effort).
        """
        fields_desc = "\n".join(f"- {k}: {v}" for k, v in schema.items())
        system = (
            "You are a structured data extraction assistant. "
            "Extract the following fields from the user's text. "
            "Return ONLY valid JSON with these keys:\n"
            f"{fields_desc}\n\n"
            "If a field cannot be found, set its value to null."
        )
        response = await self.complete(
            text, system=system, model=model, temperature=0.1,
        )

        # Try to parse JSON from the response
        try:
            # Handle responses wrapped in markdown code blocks
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            return json.loads(content)
        except (json.JSONDecodeError, IndexError):
            logger.warning("AI extraction returned non-JSON: %s", response.content[:200])
            return {"_raw": response.content, "_error": "Failed to parse JSON"}

    async def classify(
        self,
        text: str,
        *,
        categories: list[str],
        model: str | None = None,
    ) -> str:
        """Classify text into one of the given categories.

        Args:
            text: The text to classify.
            categories: List of valid category names.
            model: Override the default model.

        Returns:
            The chosen category name.
        """
        cats = ", ".join(f'"{c}"' for c in categories)
        system = (
            "You are a text classification assistant. "
            f"Classify the user's text into exactly one of these categories: {cats}. "
            "Reply with ONLY the category name, nothing else."
        )
        response = await self.complete(
            text, system=system, model=model, temperature=0.1,
        )
        result = response.content.strip().strip('"').strip("'")
        logger.debug("Classified into: %s", result)
        return result

    async def ask(
        self,
        question: str,
        *,
        context: str | None = None,
        model: str | None = None,
    ) -> str:
        """Answer a question, optionally with context.

        Args:
            question: The question to answer.
            context: Optional context or document to base the answer on.
            model: Override the default model.

        Returns:
            The answer text.
        """
        system = (
            "You are a helpful AI assistant integrated into the Pravaah "
            "backend framework. Answer questions clearly and concisely."
        )
        prompt = question
        if context:
            prompt = f"Context:\n{context}\n\nQuestion:\n{question}"

        response = await self.complete(
            prompt, system=system, model=model,
        )
        return response.content
