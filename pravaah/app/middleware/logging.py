"""Structured request logging middleware and logger bootstrap.

Provides:
- ``LoggingMiddleware`` — emits per-request access logs with method, path,
  status code, duration, and request ID.
- ``setup_logging`` — one-time logger configuration called during startup.
"""
from __future__ import annotations

import logging
import sys
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Paths that are excluded from access logging to reduce noise.
_SKIP_PATHS: frozenset[str] = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})

access_logger: logging.Logger = logging.getLogger("pravaah.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Emit structured access log entries for every HTTP request.

    Each log record includes ``method``, ``path``, ``status_code``,
    ``duration_ms``, and ``request_id`` in the ``extra`` dict so that
    structured-logging formatters (e.g. JSON) can consume them.

    Requests to health-check and documentation endpoints are silently
    skipped to keep logs focused on business traffic.

    Log levels are chosen by response status:
        - **2xx / 3xx** → ``INFO``
        - **4xx** → ``WARNING``
        - **5xx** → ``ERROR``
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request and log the outcome.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware / route handler.

        Returns:
            The HTTP response, unmodified.
        """
        # Skip noisy operational endpoints.
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        request_id: str | None = getattr(request.state, "request_id", None)

        log_data: dict[str, object] = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "request_id": request_id,
        }

        message = (
            f"{request.method} {request.url.path} "
            f"-> {response.status_code} ({duration_ms}ms)"
        )

        if response.status_code >= 500:
            access_logger.error(message, extra=log_data)
        elif response.status_code >= 400:
            access_logger.warning(message, extra=log_data)
        else:
            access_logger.info(message, extra=log_data)

        return response


def setup_logging(debug: bool = False) -> None:
    """Configure the root ``pravaah`` logger.

    Should be called **once** during application startup, before any
    requests are served.

    Args:
        debug: When ``True`` the log level is set to ``DEBUG``;
               otherwise ``INFO`` is used.
    """
    log_level = logging.DEBUG if debug else logging.INFO

    root_logger = logging.getLogger("pravaah")
    root_logger.setLevel(log_level)

    # Avoid adding duplicate handlers on repeated calls (e.g. tests).
    if not root_logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    # Prevent log records from propagating to the root logger and
    # appearing twice when a third-party root handler is configured.
    root_logger.propagate = False
