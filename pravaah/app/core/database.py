"""Pravaah async database engine.

Provides the async SQLAlchemy infrastructure used by every subsystem
that touches the database:  the CRUD engine, plugins, health checks, etc.

Architecture Notes:
    - Uses ``create_async_engine`` + ``async_sessionmaker`` for full async
      I/O with ``aiosqlite`` (SQLite) or ``asyncpg`` (PostgreSQL).
    - ``Base`` is a plain ``DeclarativeBase``.  Models that need automatic
      ``created_at`` / ``updated_at`` columns should also inherit
      ``TimestampMixin``.
    - ``get_db`` is a FastAPI dependency that yields an ``AsyncSession``
      with automatic commit-on-success / rollback-on-error semantics.
    - ``init_db`` / ``close_db`` are called by the app lifespan manager.

Scalability:
    - Swapping SQLite → PostgreSQL requires only changing the ``url`` in
      ``DatabaseConfig``; no code changes elsewhere.
    - The ``TimestampMixin`` pattern keeps timestamp logic DRY across all
      models in the framework and in plugins.
    - Using ``flush()`` inside repositories (not ``commit()``) lets the
      service layer control transaction boundaries — crucial for
      multi-step business logic.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pravaah.app.core.config import DatabaseConfig

logger = logging.getLogger("pravaah.database")

# ---------------------------------------------------------------------------
# Module-level engine & session factory (set by init_db)
# ---------------------------------------------------------------------------

engine = None  # Will be AsyncEngine after init_db()
async_session_factory: async_sessionmaker[AsyncSession] | None = None


# ---------------------------------------------------------------------------
# Declarative base & mixins
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all Pravaah models.

    Every model in the framework (core or plugin) must inherit from this
    base.  It uses the modern SQLAlchemy 2.0 declarative style with
    ``Mapped`` type annotations.
    """

    pass


class TimestampMixin:
    """Mixin that adds ``created_at`` and ``updated_at`` columns.

    Usage::

        class Customer(Base, TimestampMixin):
            __tablename__ = "customers"
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            name: Mapped[str]
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Lifecycle functions (called by app lifespan)
# ---------------------------------------------------------------------------


async def init_db(config: DatabaseConfig) -> None:
    """Initialise the async database engine and session factory.

    Creates all tables defined on ``Base.metadata`` — suitable for
    development and MVP.  Production deployments should switch to
    Alembic migrations.

    Args:
        config: Database configuration section.
    """
    global engine, async_session_factory  # noqa: PLW0603

    logger.debug("Creating async engine: %s (echo=%s)", config.url, config.echo)

    engine = create_async_engine(
        config.url,
        echo=config.echo,
        future=True,
    )

    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Auto-create tables is now done separately via create_tables()
    # after plugins are loaded and models are registered on Base.metadata.

    logger.info("Database engine initialised (%s)", config.provider)


async def create_tables() -> None:
    """Create all tables registered on ``Base.metadata``.

    Must be called **after** all plugins are loaded so that plugin
    models (which inherit from ``Base``) are included.

    This is a dev convenience — production should use Alembic migrations.
    """
    if engine is None:
        raise RuntimeError("Database engine not initialised")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created/verified")


async def close_db() -> None:
    """Dispose of the database engine and release all connections.

    Called during application shutdown to ensure clean resource cleanup.
    """
    global engine, async_session_factory  # noqa: PLW0603

    if engine is not None:
        await engine.dispose()
        logger.info("Database engine disposed")

    engine = None
    async_session_factory = None


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an ``AsyncSession``.

    The session is automatically committed on success and rolled back on
    error.  Never call ``session.commit()`` directly inside a route handler
    — the dependency handles it.

    Yields:
        An ``AsyncSession`` bound to the current request scope.

    Raises:
        RuntimeError: If ``init_db`` has not been called yet.
    """
    if async_session_factory is None:
        raise RuntimeError(
            "Database not initialised. Ensure init_db() is called before "
            "handling requests (this happens automatically in the app lifespan)."
        )

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
