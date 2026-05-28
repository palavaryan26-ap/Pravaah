"""Plugin manifest schema.

Every Pravaah plugin declares its identity and requirements through a
``PluginManifest``.  The manifest is validated at load time — malformed
manifests cause a fast, clear failure instead of cryptic import errors
at runtime.

Architecture Notes:
    - The manifest is a Pydantic model, so it validates types, defaults,
      and constraints automatically.
    - ``dependencies`` lists the *names* of other plugins that must be
      loaded first.  The plugin loader uses this for topological sorting.
    - ``enabled`` allows disabling a plugin without removing it from the
      filesystem or config.

Scalability:
    - Future versions can add fields like ``min_framework_version``,
      ``permissions``, ``config_schema`` without breaking existing plugins.
    - The manifest is serialisable (``model_dump()``) — useful for the
      CLI ``pravaah list-plugins`` command and the admin dashboard.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    """Metadata descriptor for a Pravaah plugin.

    Every plugin must provide a manifest that identifies it and declares
    its dependencies.

    Attributes:
        name: Unique plugin identifier (e.g. ``"crm"``).  Used as the
              registry key and the API route prefix.
        version: Semantic version string (e.g. ``"0.1.0"``).
        description: Human-readable one-liner explaining the plugin.
        author: Plugin author or team name.
        dependencies: Names of other plugins that must load before this
                      one.  The loader performs a topological sort.
        enabled: If ``False`` the loader skips this plugin entirely.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique plugin name (lowercase, underscores allowed)",
    )
    version: str = Field(
        default="0.1.0",
        description="Semantic version",
    )
    description: str = Field(
        default="",
        max_length=256,
        description="Short description of the plugin",
    )
    author: str = Field(
        default="",
        max_length=128,
        description="Plugin author or team",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Names of plugins that must load before this one",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the plugin should be loaded",
    )
