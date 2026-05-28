"""Pravaah application factory.

The create_app() function is the entry point for the framework.
It assembles all components following the flow-oriented architecture.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pravaah import __version__
from pravaah.app.ai.provider import create_provider
from pravaah.app.ai.router import router as ai_router
from pravaah.app.ai.service import AIService, AIServiceConfig
from pravaah.app.core.config import get_config
from pravaah.app.core.database import close_db, create_tables, init_db
from pravaah.app.core.registry import registry
from pravaah.app.events.dispatcher import init_dispatcher
from pravaah.app.plugins.loader import PluginLoader
from pravaah.app.middleware.error_handler import register_exception_handlers
from pravaah.app.middleware.logging import LoggingMiddleware, setup_logging
from pravaah.app.middleware.request_id import RequestIDMiddleware
from pravaah.app.services.health import health_router

logger = logging.getLogger("pravaah.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Startup:
        1. Load configuration
        2. Setup logging
        3. Initialize database
        4. Discover and load plugins
        5. Register plugin routes on the app

    Shutdown:
        1. Unload plugins (reverse dependency order)
        2. Close database connections
    """
    config = get_config()
    loader = PluginLoader()

    # --- Startup ---
    setup_logging(debug=config.app.debug)
    logger.info("[Pravaah] v%s starting...", __version__)
    logger.info(
        "Configuration loaded: %s mode",
        "debug" if config.app.debug else "production",
    )

    # Initialize database
    await init_db(config.database)
    logger.info("Database initialized: %s", config.database.provider)

    # Discover and load plugins
    if config.plugins.auto_discover:
        loader.discover(config.plugins.plugin_dirs)
        plugin_count = loader.load_all(app, registry)
    else:
        plugin_count = 0
        logger.info("Plugin auto-discovery disabled")

    # Create database tables AFTER plugins are loaded
    # (so plugin models are on Base.metadata)
    await create_tables()

    # Initialize event dispatcher (after plugins register hooks)
    init_dispatcher(registry)

    # Initialize AI service
    if config.ai.enabled:
        ai_provider = create_provider(
            provider_name=config.ai.provider,
            api_key=config.ai.api_key,
            model=config.ai.model,
        )
        ai_service = AIService(
            provider=ai_provider,
            config=AIServiceConfig(default_model=config.ai.model),
        )
        registry.register_service("ai", ai_service)
        logger.info("AI service enabled (provider=%s)", config.ai.provider)
    else:
        logger.info("AI service disabled")

    # Register plugin routes from registry
    for router in registry._routers:
        app.include_router(router)

    logger.info(
        "[Pravaah] Flowing on %s:%d (%d plugin(s) loaded)",
        config.app.host,
        config.app.port,
        plugin_count,
    )

    yield

    # --- Shutdown ---
    logger.info("[Pravaah] Shutting down...")
    loader.unload_all()
    await close_db()
    logger.info("Database connections closed")
    logger.info("[Pravaah] Stopped gracefully")


def create_app(config_path: str | None = None) -> FastAPI:
    """Create and configure the Pravaah FastAPI application.

    This is the main entry point. Use it with uvicorn:
        uvicorn pravaah.app.main:create_app --factory

    Args:
        config_path: Optional path to YAML config file.

    Returns:
        Configured FastAPI application instance.
    """
    # Pre-load config so it's available during app construction
    config = get_config(config_path)

    app = FastAPI(
        title="Pravaah Framework",
        description=(
            "Pravaah — Everything flows.\n\n"
            "A production-grade, AI-native, plugin-driven backend framework "
            "for scalable enterprise application development."
        ),
        version=config.app.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "Pravaah Framework",
            "url": "https://github.com/palavaryan26-ap"
        },
    )

    # --- Middleware Stack (order matters: outermost first) ---
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID (outermost — ensures all middleware has access)
    app.add_middleware(RequestIDMiddleware)

    # Logging (after request ID so it can log the ID)
    app.add_middleware(LoggingMiddleware)

    # --- Exception Handlers ---
    register_exception_handlers(app)

    # --- Built-in Routes ---
    app.include_router(health_router)
    app.include_router(ai_router)

    # --- Root endpoint ---
    @app.get("/", tags=["System"], summary="Framework info")
    async def root() -> dict[str, str]:
        """Return basic framework information."""
        return {
            "framework": "Pravaah",
            "version": config.app.version,
            "philosophy": "Everything flows.",
            "docs": "/docs",
        }

    return app
