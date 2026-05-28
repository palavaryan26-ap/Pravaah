"""Plugin discovery, loading, and lifecycle management.

The ``PluginLoader`` is responsible for:

    1. **Discovery** — scanning configured directories for Python packages
       that contain a ``PravaahPlugin`` subclass.
    2. **Validation** — checking manifests and ensuring dependencies exist.
    3. **Ordering** — topological sort so dependencies load before dependants.
    4. **Loading** — calling ``plugin.setup()`` in order.
    5. **Unloading** — calling ``plugin.teardown()`` in reverse order.

Architecture Notes:
    - Discovery uses ``importlib`` + ``pkgutil`` to find packages under
      each ``plugin_dir``.  Each package must expose a ``PravaahPlugin``
      subclass — either via a top-level ``plugin`` attribute, a ``Plugin``
      class, or by scanning the package for subclasses.
    - The loader is instantiated once by the app lifespan and manages the
      full plugin lifecycle.
    - Inspired by Django's three-stage ``AppRegistry`` init:
        Stage 1: Import + validate manifests
        Stage 2: Topological sort by dependencies
        Stage 3: Call setup() in order

Scalability:
    - Third-party plugins installed via pip can be discovered through
      ``importlib.metadata.entry_points`` (future enhancement).
    - The topological sort prevents circular dependencies and gives
      clear error messages.
    - Plugin isolation:  one plugin's setup failure is caught and logged
      but does NOT prevent other plugins from loading.

Common Pitfalls:
    - Circular dependencies between plugins are detected and reported.
    - Missing dependencies are caught before any setup() runs.
    - Plugins that raise in setup() are marked as failed but don't crash
      the framework.
"""
from __future__ import annotations

import importlib
import logging
import pkgutil
import sys
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pravaah.app.core.exceptions import PluginError
from pravaah.app.plugins.base import PravaahPlugin
from pravaah.app.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from fastapi import FastAPI
    from pravaah.app.core.registry import PravaahRegistry

logger = logging.getLogger("pravaah.plugins.loader")


class PluginLoader:
    """Discovers, validates, orders, and loads Pravaah plugins.

    Usage::

        loader = PluginLoader()
        loader.discover(["pravaah/plugins"])
        loader.load_all(app, registry)
        # ... on shutdown ...
        loader.unload_all()
    """

    def __init__(self) -> None:
        self._discovered: dict[str, PravaahPlugin] = {}
        self._loaded: list[PravaahPlugin] = []  # in load order
        self._failed: dict[str, str] = {}  # name -> error message

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, plugin_dirs: list[str]) -> dict[str, PravaahPlugin]:
        """Scan directories for plugin packages.

        Each directory is expected to contain Python packages.  Each
        package is imported and inspected for a ``PravaahPlugin`` subclass.

        The subclass is located by checking (in order):
            1. A module-level ``plugin`` attribute that is a ``PravaahPlugin`` instance
            2. A module-level ``Plugin`` class that is a ``PravaahPlugin`` subclass
            3. A ``plugin.py`` sub-module with a ``PravaahPlugin`` subclass

        Args:
            plugin_dirs: List of directory paths to scan.

        Returns:
            Dict of ``{plugin_name: plugin_instance}``.
        """
        self._discovered.clear()
        self._failed.clear()

        for plugin_dir in plugin_dirs:
            dir_path = Path(plugin_dir)
            if not dir_path.is_dir():
                logger.warning("Plugin directory not found: %s", dir_path)
                continue

            # Ensure the parent is on sys.path so imports work
            parent = str(dir_path.parent)
            if parent not in sys.path:
                sys.path.insert(0, parent)

            # Convert directory path to a dotted module path
            # e.g., "pravaah/plugins" -> "pravaah.plugins"
            module_path = str(dir_path).replace("\\", "/").replace("/", ".")

            try:
                package = importlib.import_module(module_path)
            except ImportError as e:
                logger.warning("Could not import plugin package %s: %s", module_path, e)
                continue

            # Iterate over sub-packages (each is a potential plugin)
            for importer, name, ispkg in pkgutil.iter_modules(
                package.__path__, prefix=f"{module_path}."
            ):
                if not ispkg:
                    continue  # Only packages can be plugins

                try:
                    plugin_instance = self._load_plugin_from_package(name)
                    if plugin_instance is not None:
                        manifest = plugin_instance.manifest
                        if manifest.name in self._discovered:
                            logger.warning(
                                "Duplicate plugin name '%s' — skipping %s",
                                manifest.name,
                                name,
                            )
                            continue
                        if not manifest.enabled:
                            logger.info(
                                "Plugin '%s' is disabled — skipping",
                                manifest.name,
                            )
                            continue
                        self._discovered[manifest.name] = plugin_instance
                        logger.info(
                            "Discovered plugin: %s v%s (%s)",
                            manifest.name,
                            manifest.version,
                            manifest.description or "no description",
                        )
                except Exception as exc:
                    logger.error("Failed to discover plugin from %s: %s", name, exc)
                    self._failed[name] = str(exc)

        logger.info(
            "Discovery complete: %d plugin(s) found, %d failed",
            len(self._discovered),
            len(self._failed),
        )
        return dict(self._discovered)

    def _load_plugin_from_package(self, module_path: str) -> PravaahPlugin | None:
        """Import a package and extract its PravaahPlugin subclass.

        Args:
            module_path: Dotted module path (e.g. ``"pravaah.plugins.crm"``).

        Returns:
            A ``PravaahPlugin`` instance, or ``None`` if the package
            doesn't contain one.
        """
        module = importlib.import_module(module_path)

        # Strategy 1: module-level `plugin` attribute (instance)
        plugin_attr = getattr(module, "plugin", None)
        if isinstance(plugin_attr, PravaahPlugin):
            return plugin_attr

        # Strategy 2: module-level `Plugin` class
        plugin_cls = getattr(module, "Plugin", None)
        if (
            isinstance(plugin_cls, type)
            and issubclass(plugin_cls, PravaahPlugin)
            and plugin_cls is not PravaahPlugin
        ):
            return plugin_cls()

        # Strategy 3: look inside plugin.py sub-module
        try:
            sub_module = importlib.import_module(f"{module_path}.plugin")
            for attr_name in dir(sub_module):
                attr = getattr(sub_module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PravaahPlugin)
                    and attr is not PravaahPlugin
                ):
                    return attr()
        except ImportError:
            pass

        # Strategy 4: scan all module attributes for subclasses
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PravaahPlugin)
                and attr is not PravaahPlugin
            ):
                return attr()

        return None

    # ------------------------------------------------------------------
    # Dependency resolution (topological sort)
    # ------------------------------------------------------------------

    def _resolve_load_order(self) -> list[PravaahPlugin]:
        """Topological sort of discovered plugins by dependencies.

        Uses Kahn's algorithm for deterministic ordering.

        Returns:
            Plugins sorted so that dependencies come before dependants.

        Raises:
            PluginError: If a dependency is missing or circular.
        """
        plugins = self._discovered
        plugin_names = set(plugins.keys())

        # Validate dependencies exist
        for name, plugin in plugins.items():
            for dep in plugin.manifest.dependencies:
                if dep not in plugin_names:
                    raise PluginError(
                        f"Plugin '{name}' depends on '{dep}' which is not "
                        f"available.  Discovered plugins: {sorted(plugin_names)}",
                        error_code="MISSING_DEPENDENCY",
                    )

        # Build adjacency graph
        # in_degree[x] = number of plugins that must load before x
        in_degree: dict[str, int] = {name: 0 for name in plugin_names}
        dependants: dict[str, list[str]] = {name: [] for name in plugin_names}

        for name, plugin in plugins.items():
            for dep in plugin.manifest.dependencies:
                dependants[dep].append(name)
                in_degree[name] += 1

        # Kahn's algorithm
        queue: deque[str] = deque(
            name for name, degree in in_degree.items() if degree == 0
        )
        sorted_order: list[str] = []

        while queue:
            current = queue.popleft()
            sorted_order.append(current)
            for dep_name in dependants[current]:
                in_degree[dep_name] -= 1
                if in_degree[dep_name] == 0:
                    queue.append(dep_name)

        if len(sorted_order) != len(plugin_names):
            # Circular dependency detected
            remaining = plugin_names - set(sorted_order)
            raise PluginError(
                f"Circular dependency detected among plugins: {sorted(remaining)}",
                error_code="CIRCULAR_DEPENDENCY",
            )

        return [plugins[name] for name in sorted_order]

    # ------------------------------------------------------------------
    # Loading / Unloading
    # ------------------------------------------------------------------

    def load_all(self, app: FastAPI, registry: PravaahRegistry) -> int:
        """Load all discovered plugins in dependency order.

        Calls ``plugin.setup()`` on each plugin.  If a plugin fails,
        it is logged and skipped — other plugins continue loading.

        Args:
            app: The FastAPI application instance.
            registry: The central framework registry.

        Returns:
            Number of successfully loaded plugins.
        """
        if not self._discovered:
            logger.info("No plugins to load")
            return 0

        try:
            ordered = self._resolve_load_order()
        except PluginError as exc:
            logger.error("Plugin dependency resolution failed: %s", exc.detail)
            raise

        loaded_count = 0

        for plugin in ordered:
            name = plugin.manifest.name
            try:
                plugin._do_setup(app, registry)
                registry.register_plugin(name, plugin)
                self._loaded.append(plugin)
                loaded_count += 1
            except Exception as exc:
                logger.error(
                    "Plugin '%s' failed during setup: %s",
                    name,
                    exc,
                    exc_info=True,
                )
                self._failed[name] = str(exc)

        logger.info(
            "Plugin loading complete: %d loaded, %d failed",
            loaded_count,
            len(self._failed),
        )
        return loaded_count

    def unload_all(self) -> None:
        """Unload all plugins in reverse dependency order.

        Calls ``plugin.teardown()`` on each loaded plugin.
        Errors during teardown are logged but do not propagate.
        """
        for plugin in reversed(self._loaded):
            try:
                plugin._do_teardown()
            except Exception as exc:
                logger.error(
                    "Plugin '%s' failed during teardown: %s",
                    plugin.manifest.name,
                    exc,
                )
        self._loaded.clear()
        logger.info("All plugins unloaded")

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def discovered_plugins(self) -> dict[str, PravaahPlugin]:
        """Return all discovered plugins."""
        return dict(self._discovered)

    @property
    def loaded_plugins(self) -> list[PravaahPlugin]:
        """Return all successfully loaded plugins (in load order)."""
        return list(self._loaded)

    @property
    def failed_plugins(self) -> dict[str, str]:
        """Return plugins that failed: ``{name: error_message}``."""
        return dict(self._failed)

    def summary(self) -> dict[str, Any]:
        """Return a loader summary for CLI / dashboard display."""
        return {
            "discovered": len(self._discovered),
            "loaded": len(self._loaded),
            "failed": len(self._failed),
            "plugins": [
                {
                    "name": p.manifest.name,
                    "version": p.manifest.version,
                    "description": p.manifest.description,
                }
                for p in self._loaded
            ],
            "errors": self._failed,
        }
