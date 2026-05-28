"""AI REST endpoints.

Provides HTTP endpoints for the AI service layer so that plugins,
frontends, and external clients can use AI capabilities via the API.

Endpoints:
    POST /ai/complete    — raw chat completion
    POST /ai/summarize   — summarise text
    POST /ai/extract     — extract structured data
    POST /ai/classify    — classify text into categories
    POST /ai/ask         — answer a question (with optional context)
"""
# NOTE: Do NOT use `from __future__ import annotations` here.
# FastAPI inspects type annotations at runtime for dependency injection.

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("pravaah.ai.router")

router = APIRouter(prefix="/ai", tags=["AI"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class CompleteRequest(BaseModel):
    """Request body for /ai/complete."""

    prompt: str = Field(..., min_length=1, description="The user prompt")
    system: str | None = Field(default=None, description="Optional system message")
    model: str | None = Field(default=None, description="Model override")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=16384)


class CompleteResponse(BaseModel):
    """Response body for /ai/complete."""

    content: str
    model: str
    usage: dict[str, int] = {}


class SummarizeRequest(BaseModel):
    """Request body for /ai/summarize."""

    text: str = Field(..., min_length=1, description="Text to summarise")
    max_length: int = Field(default=200, ge=10, le=2000, description="Max words")
    model: str | None = None


class SummarizeResponse(BaseModel):
    """Response body for /ai/summarize."""

    summary: str
    original_length: int
    summary_length: int


class ExtractRequest(BaseModel):
    """Request body for /ai/extract."""

    text: str = Field(..., min_length=1, description="Source text")
    schema_def: dict[str, str] = Field(
        ...,
        alias="schema",
        description="Field definitions: {field_name: description}",
    )
    model: str | None = None


class ExtractResponse(BaseModel):
    """Response body for /ai/extract."""

    data: dict[str, Any]


class ClassifyRequest(BaseModel):
    """Request body for /ai/classify."""

    text: str = Field(..., min_length=1, description="Text to classify")
    categories: list[str] = Field(
        ..., min_length=2, description="Possible categories"
    )
    model: str | None = None


class ClassifyResponse(BaseModel):
    """Response body for /ai/classify."""

    category: str
    text_preview: str


class AskRequest(BaseModel):
    """Request body for /ai/ask."""

    question: str = Field(..., min_length=1, description="The question")
    context: str | None = Field(default=None, description="Optional context")
    model: str | None = None


class AskResponse(BaseModel):
    """Response body for /ai/ask."""

    answer: str


# ---------------------------------------------------------------------------
# Helper to get AI service
# ---------------------------------------------------------------------------


def _get_ai_service():
    """Get the AI service from the registry."""
    from pravaah.app.core.registry import registry

    ai = registry.get_service("ai")
    if ai is None:
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. Enable it in config "
                   "(ai.enabled=true) and provide an API key.",
        )
    return ai


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/complete",
    response_model=CompleteResponse,
    summary="AI Completion",
    description="Generate a raw AI completion from a prompt.",
)
async def ai_complete(req: CompleteRequest) -> CompleteResponse:
    """Generate an AI completion."""
    ai = _get_ai_service()
    response = await ai.complete(
        req.prompt,
        system=req.system,
        model=req.model,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    return CompleteResponse(
        content=response.content,
        model=response.model,
        usage=response.usage,
    )


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize Text",
    description="Generate a concise summary of the provided text.",
)
async def ai_summarize(req: SummarizeRequest) -> SummarizeResponse:
    """Summarise text."""
    ai = _get_ai_service()
    summary = await ai.summarize(req.text, max_length=req.max_length, model=req.model)
    return SummarizeResponse(
        summary=summary,
        original_length=len(req.text),
        summary_length=len(summary),
    )


@router.post(
    "/extract",
    response_model=ExtractResponse,
    summary="Extract Structured Data",
    description="Extract structured fields from unstructured text.",
)
async def ai_extract(req: ExtractRequest) -> ExtractResponse:
    """Extract structured data from text."""
    ai = _get_ai_service()
    data = await ai.extract(req.text, schema=req.schema_def, model=req.model)
    return ExtractResponse(data=data)


@router.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Classify Text",
    description="Classify text into one of the provided categories.",
)
async def ai_classify(req: ClassifyRequest) -> ClassifyResponse:
    """Classify text into a category."""
    ai = _get_ai_service()
    category = await ai.classify(req.text, categories=req.categories, model=req.model)
    return ClassifyResponse(
        category=category,
        text_preview=req.text[:100],
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask AI",
    description="Ask the AI a question with optional context.",
)
async def ai_ask(req: AskRequest) -> AskResponse:
    """Answer a question."""
    ai = _get_ai_service()
    answer = await ai.ask(req.question, context=req.context, model=req.model)
    return AskResponse(answer=answer)
