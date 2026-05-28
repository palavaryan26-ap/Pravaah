"""Request ID injection middleware for distributed tracing.

Ensures every request carries a unique correlation ID, either
forwarded from an upstream caller via the ``X-Request-ID`` header
or generated as a fresh UUID4.
"""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a unique request ID to every HTTP request.

    Behaviour:
        1. If the incoming request contains an ``X-Request-ID`` header the
           value is reused (supports distributed tracing across services).
        2. Otherwise a new UUID4 is generated.
        3. The ID is stored on ``request.state.request_id`` so that
           downstream handlers and other middleware can access it.
        4. The ``X-Request-ID`` header is added to the outgoing response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request and inject the request ID.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware / route handler.

        Returns:
            The HTTP response with ``X-Request-ID`` header attached.
        """
        # Prefer an existing header for distributed-tracing propagation.
        request_id: str = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4()),
        )

        # Make accessible to other middleware and route handlers.
        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
