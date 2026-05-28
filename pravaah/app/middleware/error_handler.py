"""Global exception handlers for the Pravaah framework.

Registers structured JSON error responses for all exception types,
ensuring consistent error formatting across the API surface.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pravaah.app.core.exceptions import PravaahError

logger = logging.getLogger("pravaah.errors")


def _get_request_id(request: Request) -> str | None:
    """Extract request ID from request state if available.

    Args:
        request: The incoming HTTP request.

    Returns:
        The request ID string, or None if not set.
    """
    return getattr(request.state, "request_id", None)


def _build_error_response(
    *,
    status_code: int,
    code: str,
    detail: str,
    request_id: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Build a standardised JSON error response.

    Args:
        status_code: HTTP status code for the response.
        code: Machine-readable error code (e.g. ``NOT_FOUND``).
        detail: Human-readable error description.
        request_id: Optional request correlation ID.
        errors: Optional list of field-level validation errors.

    Returns:
        A ``JSONResponse`` with the Pravaah error envelope.
    """
    body: dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "detail": detail,
        },
    }
    if request_id is not None:
        body["error"]["request_id"] = request_id
    if errors is not None:
        body["error"]["errors"] = errors

    return JSONResponse(status_code=status_code, content=body)


async def _handle_pravaah_error(
    request: Request,
    exc: PravaahError,
) -> JSONResponse:
    """Handle ``PravaahError`` and its subclasses.

    Logs at WARNING for 4xx and ERROR for 5xx status codes.

    Args:
        request: The incoming HTTP request.
        exc: The raised ``PravaahError``.

    Returns:
        Structured JSON error response.
    """
    request_id = _get_request_id(request)
    status_code = getattr(exc, "status_code", 500)
    error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
    detail = str(exc)

    if status_code >= 500:
        logger.error(
            "Server error: %s (code=%s, request_id=%s)",
            detail,
            error_code,
            request_id,
            exc_info=exc,
        )
    else:
        logger.warning(
            "Client error: %s (code=%s, request_id=%s)",
            detail,
            error_code,
            request_id,
        )

    return _build_error_response(
        status_code=status_code,
        code=error_code,
        detail=detail,
        request_id=request_id,
    )


async def _handle_validation_error(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic / FastAPI request validation errors.

    Transforms the raw validation error list into a consistent
    field-level error structure.

    Args:
        request: The incoming HTTP request.
        exc: The raised ``RequestValidationError``.

    Returns:
        422 JSON response with structured field errors.
    """
    request_id = _get_request_id(request)
    field_errors: list[dict[str, Any]] = []

    for err in exc.errors():
        field_errors.append(
            {
                "field": " -> ".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Validation error"),
                "type": err.get("type", "value_error"),
            }
        )

    logger.warning(
        "Validation error on %s %s (request_id=%s): %d field(s)",
        request.method,
        request.url.path,
        request_id,
        len(field_errors),
    )

    return _build_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        detail="Request validation failed",
        request_id=request_id,
        errors=field_errors,
    )


async def _handle_unhandled_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for unexpected exceptions.

    Always returns a generic 500 message so that internal details
    are never leaked to the client.

    Args:
        request: The incoming HTTP request.
        exc: The unhandled exception.

    Returns:
        500 JSON response with a generic error message.
    """
    request_id = _get_request_id(request)

    logger.error(
        "Unhandled exception on %s %s (request_id=%s): %s",
        request.method,
        request.url.path,
        request_id,
        exc,
        exc_info=exc,
    )

    return _build_error_response(
        status_code=500,
        code="INTERNAL_ERROR",
        detail="An unexpected error occurred. Please try again later.",
        request_id=request_id,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application.

    This should be called once during application startup to wire up
    structured error responses for:

    - ``PravaahError`` (and subclasses) → appropriate status + error code
    - ``RequestValidationError`` → 422 with field-level details
    - ``Exception`` → 500 catch-all with safe generic message

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(PravaahError, _handle_pravaah_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unhandled_exception)  # type: ignore[arg-type]
