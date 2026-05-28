"""Pravaah AI layer.

Provides AI capabilities through an abstract provider interface,
a high-level service, and REST endpoints.

Public API::

    from pravaah.app.ai import AIService, AIProvider, create_provider
    from pravaah.app.ai.provider import AIMessage, AIResponse
    from pravaah.app.ai.router import router as ai_router
"""
from __future__ import annotations

from pravaah.app.ai.provider import (
    AIMessage,
    AIProvider,
    AIResponse,
    MockProvider,
    OpenAIProvider,
    create_provider,
)
from pravaah.app.ai.service import AIService, AIServiceConfig

__all__ = [
    "AIMessage",
    "AIProvider",
    "AIResponse",
    "AIService",
    "AIServiceConfig",
    "MockProvider",
    "OpenAIProvider",
    "create_provider",
]
