"""Hello World plugin — verifies the plugin system works.

This is a minimal plugin used for Phase 2 verification.  It will be
removed once the CRM demo plugin is built in Phase 7.
"""
from __future__ import annotations

from fastapi import APIRouter

from pravaah.app.plugins.base import PravaahPlugin
from pravaah.app.plugins.manifest import PluginManifest


class HelloPlugin(PravaahPlugin):
    """Minimal plugin that registers a single greeting endpoint."""

    manifest = PluginManifest(
        name="hello",
        version="0.1.0",
        description="Hello World verification plugin",
        author="Pravaah Team",
    )

    def setup(self, app, registry):
        """Register the /hello endpoint."""
        router = APIRouter(prefix="/hello", tags=["Hello Plugin"])

        @router.get("/", summary="Greeting")
        async def hello():
            return {
                "message": "Hello from the Pravaah plugin system!",
                "plugin": self.manifest.name,
                "version": self.manifest.version,
            }

        @router.get("/manifest", summary="Plugin manifest")
        async def manifest():
            return self.manifest.model_dump()

        self.register_routes(router)
