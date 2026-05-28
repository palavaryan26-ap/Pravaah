"""Health check service for the Pravaah framework.

Exposes a ``GET /health`` endpoint that reports on application status,
database connectivity, loaded plugins, and uptime.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

import pravaah
from pravaah.app.core import database as db_module
from pravaah.app.core.registry import registry

logger = logging.getLogger("pravaah.health")

health_router = APIRouter(tags=["System"])

# Captured at module-load time so uptime can be calculated.
_start_time: float = time.time()


async def _check_database() -> str:
    """Verify database connectivity by executing a trivial query.

    Returns:
        ``"connected"`` if the query succeeds, ``"disconnected"`` otherwise.
    """
    try:
        if db_module.engine is None:
            return "disconnected"
        async with db_module.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "connected"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database health check failed: %s", exc)
        return "disconnected"


@health_router.get(
    "/health",
    summary="Health check",
    description="Returns the current health status of the Pravaah framework.",
    response_model=None,
)
async def health_check() -> dict[str, Any]:
    """Return a health report for the running application.

    The response includes:
    - **status** — always ``"healthy"`` (the endpoint itself being reachable
      implies the process is alive).
    - **version** — the installed ``pravaah`` package version.
    - **framework** — fixed ``"Pravaah"`` identifier.
    - **database** — ``"connected"`` or ``"disconnected"``.
    - **plugins_loaded** — number of plugins registered in the plugin registry.
    - **uptime_seconds** — seconds since the health module was loaded.

    Returns:
        A dict serialised as JSON by FastAPI.
    """
    db_status = await _check_database()
    plugins = registry.list_plugins()

    return {
        "status": "healthy",
        "version": pravaah.__version__,
        "framework": "Pravaah",
        "database": db_status,
        "plugins_loaded": len(plugins),
        "uptime_seconds": round(time.time() - _start_time, 2),
    }
