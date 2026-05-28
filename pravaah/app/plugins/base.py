"""Abstract base class for Pravaah plugins.

``PravaahPlugin`` defines the contract every plugin must follow.  It
provides lifecycle hooks and convenience methods that delegate to the
central registry.

Architecture Notes:
    - Inspired by Django's ``AppConfig.ready()`` and Frappe's
      ``hooks.py`` — but compressed into a single class with explicit
      lifecycle stages.
    - The lifecycle is:
        1. **Instantiation** — plugin is imported, ``__init__`` runs
        2. **setup()** — called by the loader in dependency order;
           register models, routes, hooks, services here.
        3. **teardown()** — called on shutdown in reverse order.
    - Plugins receive the ``FastAPI`` app and ``PravaahRegistry`` via
      ``setup()`` so they don't need to import globals.  This keeps
      plugins testable in isolation.

Scalability:
    - Subclassing is the extension mechanism:  ``class CRMPlugin(PravaahPlugin)``
    - Helper methods (``register_model``, etc.) inject the plugin name
      automatically, making introspection ("which plugin registered this
      model?") trivial.
    - The base class is intentionally minimal — advanced plugins can
      override any hook.

Example::

    from pravaah.app.plugins.base import PravaahPlugin
    from pravaah.app.plugins.manifest import PluginManifest

    class CRMPlugin(PravaahPlugin):
        manifest = PluginManifest(
            name="crm",
            version="0.1.0",
            description="Customer Relationship Management",
        )

        def setup(self, app, registry):
            from .models import Customer, Lead
            from .schemas import CustomerCreate, CustomerUpdate, CustomerRead
            self.register_model("Customer", Customer,
                                CustomerCreate, CustomerUpdate, CustomerRead)
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

from pravaah.app.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from fastapi import APIRouter, FastAPI
    from pravaah.app.core.registry import PravaahRegistry

logger = logging.getLogger("pravaah.plugins")


class PravaahPlugin(ABC):
    """Abstract base class for all Pravaah plugins.

    Subclass this and implement ``setup()`` to create a plugin.
    The ``manifest`` class attribute is required.

    Attributes:
        manifest: Plugin metadata (name, version, dependencies, etc.).
    """

    manifest: PluginManifest

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate that subclasses define a manifest."""
        super().__init_subclass__(**kwargs)
        # Skip validation for intermediate abstract classes
        if getattr(cls, "__abstractmethods__", None):
            return
        if not hasattr(cls, "manifest") or not isinstance(
            getattr(cls, "manifest", None), PluginManifest
        ):
            raise TypeError(
                f"Plugin class '{cls.__name__}' must define a "
                f"'manifest' class attribute of type PluginManifest"
            )

    def __init__(self) -> None:
        self._registry: PravaahRegistry | None = None
        self._app: FastAPI | None = None

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    @abstractmethod
    def setup(self, app: FastAPI, registry: PravaahRegistry) -> None:
        """Called when the plugin is loaded.

        Register models, routes, hooks, and services here.
        Called in dependency order — if plugin A depends on plugin B,
        B's ``setup()`` runs first.

        Args:
            app: The FastAPI application instance.
            registry: The central framework registry.
        """
        ...

    def teardown(self) -> None:
        """Called when the application shuts down.

        Override to release resources (close connections, cancel tasks,
        flush caches).  Called in reverse dependency order.
        """
        pass

    # ------------------------------------------------------------------
    # Convenience registration methods
    # ------------------------------------------------------------------

    def _ensure_setup(self) -> PravaahRegistry:
        """Return the registry, raising if setup() hasn't been called."""
        if self._registry is None:
            raise RuntimeError(
                f"Plugin '{self.manifest.name}' tried to register components "
                f"before setup() was called by the framework."
            )
        return self._registry

    def register_model(
        self,
        name: str,
        model: type,
        create_schema: type,
        update_schema: type,
        read_schema: type,
    ) -> None:
        """Register a model with the framework.

        Convenience wrapper around ``registry.register_model()`` that
        automatically tags the registration with this plugin's name.

        Args:
            name: Model name (e.g. ``"Customer"``).
            model: SQLAlchemy model class.
            create_schema: Pydantic schema for POST payloads.
            update_schema: Pydantic schema for PUT/PATCH payloads.
            read_schema: Pydantic schema for GET responses.
        """
        reg = self._ensure_setup()
        reg.register_model(
            name=name,
            model=model,
            create_schema=create_schema,
            update_schema=update_schema,
            read_schema=read_schema,
            plugin=self.manifest.name,
        )

    def register_routes(self, router: APIRouter) -> None:
        """Register a FastAPI router with the framework.

        Args:
            router: The ``APIRouter`` to mount.
        """
        reg = self._ensure_setup()
        reg.register_router(router)

    def register_hook(
        self,
        event_name: str,
        handler: Callable[..., Any],
        *,
        priority: int = 0,
    ) -> None:
        """Register an event hook with the framework.

        Args:
            event_name: Event identifier (e.g. ``"on_create:Customer"``).
            handler: Callable to invoke when the event fires.
            priority: Execution order — lower runs first.
        """
        reg = self._ensure_setup()
        reg.register_hook(
            event_name=event_name,
            handler=handler,
            priority=priority,
            plugin=self.manifest.name,
        )

    def register_service(self, name: str, service: Any) -> None:
        """Register a shared service instance.

        Args:
            name: Service identifier (e.g. ``"crm_service"``).
            service: The service instance.
        """
        reg = self._ensure_setup()
        reg.register_service(name=name, service=service)

    # ------------------------------------------------------------------
    # Internal — called by the plugin loader
    # ------------------------------------------------------------------

    def _do_setup(self, app: FastAPI, registry: PravaahRegistry) -> None:
        """Internal: bind the app and registry, then call user setup().

        This is called by the plugin loader — plugins should NOT call
        this directly.
        """
        self._app = app
        self._registry = registry
        logger.info(
            "Setting up plugin: %s v%s",
            self.manifest.name,
            self.manifest.version,
        )
        self.setup(app, registry)
        logger.info("Plugin ready: %s", self.manifest.name)

    def _do_teardown(self) -> None:
        """Internal: call user teardown() and clean up references."""
        logger.info("Tearing down plugin: %s", self.manifest.name)
        self.teardown()
        self._app = None
        self._registry = None

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.manifest.name!r} v={self.manifest.version}>"
