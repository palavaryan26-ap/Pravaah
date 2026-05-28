"""Pravaah central registry.

The ``PravaahRegistry`` is the **nervous system** of the framework — it
is the single place where plugins, models, hooks, routes, and services
are registered and discovered.

Architecture Notes:
    - A module-level singleton (``registry``) is imported by all subsystems
      that need to register or query components.
    - Registration is **append-only** during startup; runtime mutation is
      not expected, so no locking is needed for the MVP.
    - ``ModelRegistration`` and ``HookRegistration`` are data classes that
      carry the metadata needed by the CRUD engine and event dispatcher
      respectively.

Scalability:
    - The registry pattern decouples producers (plugins) from consumers
      (CRUD engine, event dispatcher, CLI introspection).
    - Adding a new registry dimension (e.g., scheduled jobs, AI workflows)
      is a one-liner:  add a new ``dict`` + register/get methods.
    - Introspection methods (``list_*``) power the CLI ``nexus list-plugins``
      and the future admin dashboard.

Inspired by:
    - Django's ``AppRegistry`` — multi-stage registration
    - Framework-M's DocType discovery — metadata-first registration
    - Frappe's ``hooks.py`` — centralised hook mapping
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import APIRouter

logger = logging.getLogger("pravaah.registry")


# ---------------------------------------------------------------------------
# Registration data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelRegistration:
    """Metadata for a registered model.

    Stored in the registry when a plugin calls ``register_model()``.
    The CRUD engine reads these to auto-generate routers.

    Attributes:
        model: The SQLAlchemy model class.
        create_schema: Pydantic schema for creation payloads.
        update_schema: Pydantic schema for update payloads.
        read_schema: Pydantic schema for read responses.
        plugin: Name of the plugin that registered this model.
    """

    model: type
    create_schema: type
    update_schema: type
    read_schema: type
    plugin: str = ""


@dataclass
class HookRegistration:
    """Metadata for a registered event hook.

    Attributes:
        handler: The callable to invoke when the event fires.
        priority: Lower numbers run first (default 0).
        plugin: Name of the plugin that registered this hook.
    """

    handler: Callable[..., Any]
    priority: int = 0
    plugin: str = ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class PravaahRegistry:
    """Central registry for all framework components.

    The registry tracks:
        - **Plugins** — loaded plugin instances keyed by name
        - **Models** — SQLAlchemy models + Pydantic schemas
        - **Hooks** — event handlers grouped by event name
        - **Routers** — FastAPI routers to be mounted on the app
        - **Services** — shared service instances (AI, email, etc.)
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Any] = {}
        self._models: dict[str, ModelRegistration] = {}
        self._hooks: dict[str, list[HookRegistration]] = {}
        self._routers: list[APIRouter] = []
        self._services: dict[str, Any] = {}

    # -- Plugin registration ------------------------------------------------

    def register_plugin(self, name: str, plugin: Any) -> None:
        """Register a loaded plugin instance.

        Args:
            name: Unique plugin identifier (e.g. ``"crm"``).
            plugin: The plugin instance (typically a ``NexusPlugin`` subclass).

        Raises:
            ValueError: If a plugin with this name is already registered.
        """
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' is already registered")
        self._plugins[name] = plugin
        logger.info("Plugin registered: %s", name)

    def get_plugin(self, name: str) -> Any | None:
        """Retrieve a registered plugin by name."""
        return self._plugins.get(name)

    def list_plugins(self) -> dict[str, Any]:
        """Return all registered plugins as ``{name: instance}``."""
        return dict(self._plugins)

    # -- Model registration -------------------------------------------------

    def register_model(
        self,
        name: str,
        model: type,
        create_schema: type,
        update_schema: type,
        read_schema: type,
        *,
        plugin: str = "",
    ) -> None:
        """Register a model with its Pydantic schemas.

        The CRUD engine reads these registrations to auto-generate
        REST endpoints.

        Args:
            name: Model name (e.g. ``"Customer"``).
            model: SQLAlchemy model class.
            create_schema: Pydantic schema for ``POST`` payloads.
            update_schema: Pydantic schema for ``PUT/PATCH`` payloads.
            read_schema: Pydantic schema for responses.
            plugin: Name of the registering plugin (for introspection).
        """
        if name in self._models:
            raise ValueError(f"Model '{name}' is already registered")
        self._models[name] = ModelRegistration(
            model=model,
            create_schema=create_schema,
            update_schema=update_schema,
            read_schema=read_schema,
            plugin=plugin,
        )
        logger.info("Model registered: %s (plugin=%s)", name, plugin or "core")

    def get_model(self, name: str) -> ModelRegistration | None:
        """Retrieve a model registration by name."""
        return self._models.get(name)

    def list_models(self) -> list[str]:
        """Return all registered model names."""
        return list(self._models.keys())

    # -- Hook registration --------------------------------------------------

    def register_hook(
        self,
        event_name: str,
        handler: Callable[..., Any],
        *,
        priority: int = 0,
        plugin: str = "",
    ) -> None:
        """Register an event hook handler.

        Handlers for the same event are sorted by priority (ascending)
        when retrieved.

        Args:
            event_name: Event identifier (e.g. ``"on_create:Customer"``).
            handler: The callable to invoke when the event fires.
            priority: Execution order — lower runs first.
            plugin: Name of the registering plugin.
        """
        registration = HookRegistration(
            handler=handler,
            priority=priority,
            plugin=plugin,
        )
        self._hooks.setdefault(event_name, []).append(registration)
        logger.debug(
            "Hook registered: %s -> %s (priority=%d, plugin=%s)",
            event_name,
            handler.__qualname__,
            priority,
            plugin or "core",
        )

    def get_hooks(self, event_name: str) -> list[HookRegistration]:
        """Return all hook registrations for an event, sorted by priority."""
        hooks = self._hooks.get(event_name, [])
        return sorted(hooks, key=lambda h: h.priority)

    def list_hooks(self) -> dict[str, int]:
        """Return a summary of registered hooks: ``{event_name: handler_count}``."""
        return {event: len(handlers) for event, handlers in self._hooks.items()}

    # -- Router registration ------------------------------------------------

    def register_router(self, router: APIRouter) -> None:
        """Register a FastAPI router for mounting on the application.

        Args:
            router: The ``APIRouter`` instance to include.
        """
        self._routers.append(router)
        logger.debug("Router registered (%d total)", len(self._routers))

    # -- Service registration -----------------------------------------------

    def register_service(self, name: str, service: Any) -> None:
        """Register a shared service instance.

        Services are singleton-like objects (e.g. AI provider, email
        sender) that plugins and routes can retrieve by name.

        Args:
            name: Unique service identifier (e.g. ``"ai"``).
            service: The service instance.
        """
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered")
        self._services[name] = service
        logger.info("Service registered: %s", name)

    def get_service(self, name: str) -> Any | None:
        """Retrieve a registered service by name."""
        return self._services.get(name)

    # -- Utility ------------------------------------------------------------

    def clear(self) -> None:
        """Clear the registry (useful for testing)."""
        self._plugins.clear()
        self._models.clear()
        self._hooks.clear()
        self._routers.clear()
        self._services.clear()

    # -- Introspection ------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """Return a full registry summary for debugging / CLI output."""
        return {
            "plugins": list(self._plugins.keys()),
            "models": list(self._models.keys()),
            "hooks": self.list_hooks(),
            "routers": len(self._routers),
            "services": list(self._services.keys()),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

registry = PravaahRegistry()
