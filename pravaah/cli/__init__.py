"""Pravaah CLI package.

Entry point::

    python -m pravaah.cli.main
    # or via console_scripts:
    pravaah --help
"""
from pravaah.cli.main import app, main

__all__ = ["app", "main"]
