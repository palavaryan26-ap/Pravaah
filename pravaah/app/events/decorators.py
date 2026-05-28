"""Convenience decorators for registering event hooks.

These decorators provide a clean, declarative way for plugins to
register event handlers without directly touching the registry.

Architecture Notes:
    - Decorators **mark** functions with metadata but do NOT register
      them immediately (the registry may not exist at import time).
    - The ``PravaahPlugin.setup()`` method should call
      ``register_hook()`` for each decorated handler.
    - The ``collect_hooks()`` helper scans a module for decorated
      functions and returns registration metadata.
    - This two-phase approach (mark at import, register at setup)
      avoids import-order issues and keeps plugins testable.

Usage in a plugin::

    from pravaah.app.events.decorators import on_event, before_create, after_create

    @after_create("Customer")
    async def notify_sales(ctx):
        print(f"New customer created: {ctx.data}")

    @before_create("Invoice")
    async def validate_invoice(ctx):
        if ctx.data.get("amount", 0) <= 0:
            raise ValueError("Invoice amount must be positive")

    # In plugin setup():
    class MyPlugin(PravaahPlugin):
        def setup(self, app, registry):
            from . import hooks
            for event, handler, priority in collect_hooks(hooks):
                self.register_hook(event, handler, priority=priority)
"""
from __future__ import annotations

import inspect
import types
from typing import Any, Callable


# Marker attribute set on decorated functions
_HOOK_ATTR = "_pravaah_hook"


def on_event(
    event_name: str,
    *,
    priority: int = 0,
) -> Callable[..., Any]:
    """Register a function as a handler for a named event.

    Args:
        event_name: The event to listen for
                    (e.g. ``"custom:order_placed"``).
        priority: Execution order — lower runs first.

    Returns:
        A decorator that marks the function.

    Example::

        @on_event("custom:payment_received")
        async def handle_payment(ctx):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        setattr(func, _HOOK_ATTR, {
            "event": event_name,
            "priority": priority,
        })
        return func
    return decorator


# ---------------------------------------------------------------------------
# CRUD lifecycle convenience decorators
# ---------------------------------------------------------------------------


def before_create(model_name: str, *, priority: int = 0) -> Callable[..., Any]:
    """Decorator: run before a record is created.

    Example::

        @before_create("Customer")
        async def validate_customer(ctx):
            if not ctx.data.get("email"):
                raise ValueError("Email is required")
    """
    return on_event(f"before_create:{model_name}", priority=priority)


def after_create(model_name: str, *, priority: int = 0) -> Callable[..., Any]:
    """Decorator: run after a record is created."""
    return on_event(f"after_create:{model_name}", priority=priority)


def before_update(model_name: str, *, priority: int = 0) -> Callable[..., Any]:
    """Decorator: run before a record is updated."""
    return on_event(f"before_update:{model_name}", priority=priority)


def after_update(model_name: str, *, priority: int = 0) -> Callable[..., Any]:
    """Decorator: run after a record is updated."""
    return on_event(f"after_update:{model_name}", priority=priority)


def before_delete(model_name: str, *, priority: int = 0) -> Callable[..., Any]:
    """Decorator: run before a record is deleted."""
    return on_event(f"before_delete:{model_name}", priority=priority)


def after_delete(model_name: str, *, priority: int = 0) -> Callable[..., Any]:
    """Decorator: run after a record is deleted."""
    return on_event(f"after_delete:{model_name}", priority=priority)


# ---------------------------------------------------------------------------
# Hook collection helper
# ---------------------------------------------------------------------------


def collect_hooks(
    module: types.ModuleType,
) -> list[tuple[str, Callable[..., Any], int]]:
    """Scan a module for decorated hook functions.

    Returns a list of ``(event_name, handler, priority)`` tuples
    ready to be passed to ``register_hook()``.

    Args:
        module: The Python module to scan.

    Returns:
        List of ``(event, handler, priority)`` tuples.

    Example::

        from myapp.plugins.crm import hooks
        for event, handler, priority in collect_hooks(hooks):
            self.register_hook(event, handler, priority=priority)
    """
    results: list[tuple[str, Callable[..., Any], int]] = []

    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj) and hasattr(obj, _HOOK_ATTR):
            meta = getattr(obj, _HOOK_ATTR)
            results.append((meta["event"], obj, meta["priority"]))

    # Sort by priority for deterministic registration order
    results.sort(key=lambda x: x[2])
    return results
