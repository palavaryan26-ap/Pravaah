"""Pravaah plugin system.

The plugin system is the primary extensibility mechanism of Pravaah.
Everything in the framework — models, routes, hooks, services — is
registered through plugins.

Public API::

    from pravaah.app.plugins import PravaahPlugin, PluginManifest, PluginLoader
"""
from __future__ import annotations

from pravaah.app.plugins.base import PravaahPlugin
from pravaah.app.plugins.loader import PluginLoader
from pravaah.app.plugins.manifest import PluginManifest

__all__ = ["PravaahPlugin", "PluginLoader", "PluginManifest"]
