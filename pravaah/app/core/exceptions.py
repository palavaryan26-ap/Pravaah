"""Pravaah exception hierarchy.

All framework exceptions inherit from :class:`PravaahError` and carry
an HTTP ``status_code``, a human-readable ``detail`` message, and an
optional machine-readable ``error_code`` for programmatic handling.

Architecture Notes:
    - Every subsystem (plugins, CRUD, AI, auth) has its own exception class.
    - The global error-handler middleware (``error_handler.py``) catches
      ``PravaahError`` and maps it directly to a structured JSON response.
    - Keeping a single hierarchy makes it trivial to add new exception types
      without modifying the error-handling middleware.

Scalability:
    - Plugins can subclass any exception here to create domain-specific errors
      (e.g., ``class InvoiceNotFoundError(NotFoundError): ...``).
    - ``error_code`` enables frontends and API consumers to switch on a stable
      string rather than parsing human-readable messages.
"""
from __future__ import annotations


class PravaahError(Exception):
    """Base exception for all Pravaah framework errors.

    Every framework exception inherits from this class, ensuring a
    consistent interface for the global error handler.

    Args:
        detail: Human-readable error description.
        status_code: HTTP status code (default 500).
        error_code: Machine-readable error identifier
                    (e.g. ``"PLUGIN_NOT_FOUND"``).
    """

    def __init__(
        self,
        detail: str = "An internal error occurred",
        *,
        status_code: int = 500,
        error_code: str | None = None,
    ) -> None:
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        super().__init__(self.detail)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class ConfigError(PravaahError):
    """Raised when framework configuration is invalid or missing."""

    def __init__(
        self,
        detail: str = "Configuration error",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail, status_code=500, error_code=error_code or "CONFIG_ERROR")


# ---------------------------------------------------------------------------
# Plugin system
# ---------------------------------------------------------------------------

class PluginError(PravaahError):
    """Raised when a plugin fails to load, register, or execute."""

    def __init__(
        self,
        detail: str = "Plugin error",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail, status_code=500, error_code=error_code or "PLUGIN_ERROR")


# ---------------------------------------------------------------------------
# CRUD engine
# ---------------------------------------------------------------------------

class CRUDError(PravaahError):
    """Raised for CRUD operation failures (bad input, constraint violations)."""

    def __init__(
        self,
        detail: str = "CRUD operation failed",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail, status_code=400, error_code=error_code or "CRUD_ERROR")


class NotFoundError(PravaahError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        detail: str = "Resource not found",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail, status_code=404, error_code=error_code or "NOT_FOUND")


class ValidationError(PravaahError):
    """Raised for domain-level validation failures (beyond Pydantic)."""

    def __init__(
        self,
        detail: str = "Validation failed",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail, status_code=422, error_code=error_code or "VALIDATION_ERROR")


# ---------------------------------------------------------------------------
# Authentication & authorization
# ---------------------------------------------------------------------------

class AuthenticationError(PravaahError):
    """Raised when authentication is required but missing or invalid."""

    def __init__(
        self,
        detail: str = "Authentication required",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail, status_code=401, error_code=error_code or "AUTH_REQUIRED")


class AuthorizationError(PravaahError):
    """Raised when the authenticated user lacks permission."""

    def __init__(
        self,
        detail: str = "Insufficient permissions",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail, status_code=403, error_code=error_code or "FORBIDDEN")


# ---------------------------------------------------------------------------
# AI service layer
# ---------------------------------------------------------------------------

class AIServiceError(PravaahError):
    """Raised when the AI service is unavailable or returns an error."""

    def __init__(
        self,
        detail: str = "AI service unavailable",
        *,
        error_code: str | None = None,
    ) -> None:
        super().__init__(detail, status_code=503, error_code=error_code or "AI_SERVICE_ERROR")
