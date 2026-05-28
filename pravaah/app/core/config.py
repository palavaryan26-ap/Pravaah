"""Pravaah configuration system.

Implements a layered configuration strategy following 12-factor app principles:

    Priority (highest → lowest):
        1. Environment variables  (``PRAVAAH_APP__DEBUG=true``)
        2. YAML config file       (``config/pravaah.yaml``)
        3. Pydantic defaults      (hardcoded sensible values)

Architecture Notes:
    - Uses ``pydantic-settings`` for type-safe env var parsing with the
      ``PRAVAAH_`` prefix and ``__`` as the nested delimiter.
    - The ``from_yaml()`` class method loads a YAML file, and the resulting
      dict is merged *before* env vars are resolved — so env vars always
      win, matching 12-factor expectations.
    - A module-level singleton (``_config``) avoids re-reading the file
      on every access.  Use ``reset_config()`` in tests.

Scalability:
    - Adding a new config section is a one-liner:  define a ``BaseModel``
      and add it as a field on ``PravaahConfig``.
    - Plugins will receive the full config object and can read their own
      sections via ``config.plugins`` or custom sections.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("pravaah.config")

# ---------------------------------------------------------------------------
# Config sections
# ---------------------------------------------------------------------------


class AppConfig(BaseModel):
    """Core application settings."""

    name: str = "Pravaah"
    version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


class DatabaseConfig(BaseModel):
    """Database connection settings."""

    provider: str = "sqlite"
    url: str = "sqlite+aiosqlite:///./pravaah.db"
    echo: bool = False


class AIConfig(BaseModel):
    """AI service layer settings."""

    enabled: bool = False
    provider: str = "openai"
    api_key: str = ""
    model: str = "gpt-4o-mini"


class PluginConfig(BaseModel):
    """Plugin discovery and loading settings."""

    plugin_dirs: list[str] = ["pravaah/plugins"]
    auto_discover: bool = True


# ---------------------------------------------------------------------------
# Root config
# ---------------------------------------------------------------------------


class PravaahConfig(BaseSettings):
    """Root configuration for the Pravaah framework.

    Resolves values from environment variables (``PRAVAAH_`` prefix, ``__``
    nested delimiter) and falls back to defaults.  Call ``from_yaml()`` to
    load values from a YAML file *before* env-var resolution.

    Example env vars::

        PRAVAAH_APP__DEBUG=true
        PRAVAAH_DATABASE__URL=sqlite+aiosqlite:///./prod.db
        PRAVAAH_AI__API_KEY=sk-...
    """

    model_config = SettingsConfigDict(
        env_prefix="PRAVAAH_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    ai: AIConfig = AIConfig()
    plugins: PluginConfig = PluginConfig()

    @classmethod
    def from_yaml(cls, path: str | Path) -> PravaahConfig:
        """Load configuration from a YAML file.

        Missing keys fall back to Pydantic defaults.  Environment variables
        still override YAML values (handled by pydantic-settings).

        Args:
            path: Filesystem path to the YAML configuration file.

        Returns:
            A fully resolved ``PravaahConfig`` instance.
        """
        yaml_path = Path(path)
        yaml_data: dict[str, Any] = {}

        if yaml_path.is_file():
            with yaml_path.open("r", encoding="utf-8") as fh:
                raw = yaml.safe_load(fh)
                if isinstance(raw, dict):
                    yaml_data = raw
            logger.debug("Loaded config from %s", yaml_path)
        else:
            logger.debug("Config file not found at %s — using defaults", yaml_path)

        return cls(**yaml_data)


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_config: PravaahConfig | None = None

# Default search paths for YAML config (checked in order)
_DEFAULT_CONFIG_PATHS = [
    "config/pravaah.yaml",
    "pravaah.yaml",
]


def get_config(config_path: str | None = None) -> PravaahConfig:
    """Return the global ``PravaahConfig`` singleton.

    On first call the config is loaded from:
        1. *config_path* (if provided), or
        2. The first existing file in ``_DEFAULT_CONFIG_PATHS``, or
        3. Pure defaults + env vars.

    Subsequent calls return the cached instance.

    Args:
        config_path: Optional explicit path to the YAML config file.

    Returns:
        The framework configuration singleton.
    """
    global _config  # noqa: PLW0603

    if _config is not None:
        return _config

    if config_path:
        _config = PravaahConfig.from_yaml(config_path)
    else:
        # Search default locations
        for candidate in _DEFAULT_CONFIG_PATHS:
            if Path(candidate).is_file():
                _config = PravaahConfig.from_yaml(candidate)
                break
        else:
            # No YAML file found — pure defaults + env vars
            _config = PravaahConfig()
            logger.debug("No config file found — using defaults + env vars")

    return _config


def reset_config() -> None:
    """Clear the cached config singleton.

    Useful in test fixtures to ensure a clean config state between tests.
    """
    global _config  # noqa: PLW0603
    _config = None
