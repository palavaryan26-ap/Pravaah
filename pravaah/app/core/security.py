"""Pravaah security stubs.

Provides placeholder authentication dependencies for the MVP.

Architecture Notes:
    - ``get_current_user`` is the primary auth dependency — routes that
      need authentication inject it via ``Depends(get_current_user)``.
    - ``require_auth`` is a stricter wrapper that raises
      ``AuthenticationError`` when no user is resolved.
    - For the MVP, ``get_current_user`` always returns ``None`` (no auth).
      Swap in JWT / OAuth2 / API-key verification in a later phase.

Future Extension Points:
    - JWT bearer:  decode the ``Authorization: Bearer <token>`` header,
      verify the signature, and return the user payload.
    - OAuth2:  integrate ``fastapi.security.OAuth2AuthorizationCodeBearer``
      and validate tokens against the identity provider.
    - API keys:  hash incoming ``X-API-Key`` header with argon2 and look
      up the matching ``ApiKey`` record (inspired by Framework-M).
    - RBAC:  add ``require_role("admin")`` as a dependency that chains
      on top of ``require_auth``.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, Request

from pravaah.app.core.exceptions import AuthenticationError

logger = logging.getLogger("pravaah.security")


async def get_current_user(request: Request) -> dict[str, Any] | None:
    """Resolve the current authenticated user from the request.

    **MVP stub** — always returns ``None`` (unauthenticated).
    Replace this implementation to enable authentication.

    Args:
        request: The incoming HTTP request (provides access to
                 headers, cookies, and state).

    Returns:
        A user dict if authenticated, or ``None`` if anonymous.
    """
    # TODO: Implement JWT / API-key authentication here.
    #
    # Example (JWT):
    #   token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    #   if not token:
    #       return None
    #   payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    #   return {"id": payload["sub"], "roles": payload.get("roles", [])}
    #
    return None


async def require_auth(
    user: dict[str, Any] | None = Depends(get_current_user),
) -> dict[str, Any]:
    """FastAPI dependency that **requires** authentication.

    Use this for protected routes::

        @router.get("/profile", dependencies=[Depends(require_auth)])
        async def get_profile(user=Depends(require_auth)):
            return user

    Args:
        user: Resolved user from ``get_current_user``.

    Returns:
        The authenticated user dict.

    Raises:
        AuthenticationError: If the user is not authenticated.
    """
    if user is None:
        raise AuthenticationError("Authentication required to access this resource")
    return user
