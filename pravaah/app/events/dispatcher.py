"""Event dispatcher — fires events and collects handler results.

The dispatcher reads handlers from the central ``PravaahRegistry`` and
invokes them in priority order.  It supports both sync and async
handlers, error isolation, and structured event context.

Architecture Notes:
    - Events are identified by string names following a convention:
        - CRUD lifecycle:  ``before_create:ModelName``, ``after_update:ModelName``
        - Custom events:   ``custom:order_placed``, ``custom:payment_received``
        - System events:   ``system:startup``, ``system:shutdown``
    - Handlers receive an ``EventContext`` dataclass with the event name,
      model name (if applicable), the data payload, and optional metadata.
    - Each handler runs in its own try/except — one handler's failure
      does NOT prevent other handlers from executing.
    - ``before_*`` handlers can modify the data payload (e.g. validate,
      enrich, or reject by raising an exception).
    - ``after_*`` handlers receive the final data and are fire-and-forget.

Scalability:
    - Plugins register hooks via ``registry.register_hook()`` at setup
      time.  The dispatcher doesn't import or know about plugins.
    - Adding a new event type is free — just fire it with a new name.
    - The ``EventResult`` tracks success/failure per handler for
      debugging and observability.

Inspired by:
    - Framework-M's DocType hooks (validate, before_save, after_save)
    - Django signals (pre_save, post_save)
    - Node.js EventEmitter pattern
"""
from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any

from pravaah.app.core.registry import PravaahRegistry

logger = logging.getLogger("pravaah.events")


# ---------------------------------------------------------------------------
# Event data structures
# ---------------------------------------------------------------------------


@dataclass
class EventContext:
    """Context object passed to every event handler.

    Attributes:
        event: The full event name (e.g. ``"after_create:Customer"``).
        action: The action part (e.g. ``"after_create"``).
        model_name: The model part (e.g. ``"Customer"``), or empty for
                    non-model events.
        data: The primary data payload (e.g. the created record dict).
        metadata: Additional context (e.g. ``{"user_id": 42}``).
    """

    event: str
    action: str = ""
    model_name: str = ""
    data: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Parse action and model_name from the event string."""
        if ":" in self.event and not self.action:
            parts = self.event.split(":", 1)
            self.action = parts[0]
            self.model_name = parts[1] if len(parts) > 1 else ""


@dataclass
class HandlerResult:
    """Result of a single handler invocation.

    Attributes:
        handler_name: Qualified name of the handler function.
        plugin: Name of the plugin that registered the handler.
        success: Whether the handler completed without error.
        error: Error message if the handler failed.
        result: Return value from the handler (if any).
    """

    handler_name: str
    plugin: str = ""
    success: bool = True
    error: str | None = None
    result: Any = None


@dataclass
class EventResult:
    """Aggregate result of dispatching an event.

    Attributes:
        event: The event name that was fired.
        handler_count: Number of handlers that were invoked.
        results: Individual results from each handler.
        all_succeeded: True if every handler completed without error.
    """

    event: str
    handler_count: int = 0
    results: list[HandlerResult] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        """Return True if every handler succeeded."""
        return all(r.success for r in self.results)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


class EventDispatcher:
    """Fires events and invokes registered handlers.

    Usage::

        dispatcher = EventDispatcher(registry)

        # Fire a CRUD lifecycle event
        result = await dispatcher.dispatch(
            "after_create:Customer",
            data={"id": 1, "name": "Alice"},
        )

        # Fire a custom event
        result = await dispatcher.dispatch(
            "custom:order_placed",
            data=order_dict,
            metadata={"user_id": 42},
        )
    """

    def __init__(self, registry: PravaahRegistry) -> None:
        self._registry = registry

    async def dispatch(
        self,
        event: str,
        *,
        data: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> EventResult:
        """Fire an event and invoke all registered handlers.

        Handlers are called in priority order (lower numbers first).
        Each handler receives an ``EventContext`` and runs in its own
        try/except for error isolation.

        Args:
            event: Event name (e.g. ``"after_create:Customer"``).
            data: Primary data payload.
            metadata: Additional context dict.

        Returns:
            An ``EventResult`` with per-handler results.
        """
        ctx = EventContext(
            event=event,
            data=data,
            metadata=metadata or {},
        )

        hooks = self._registry.get_hooks(event)
        result = EventResult(event=event, handler_count=len(hooks))

        if not hooks:
            logger.debug("No handlers for event: %s", event)
            return result

        logger.debug(
            "Dispatching event '%s' to %d handler(s)",
            event,
            len(hooks),
        )

        for hook in hooks:
            handler = hook.handler
            handler_name = getattr(handler, "__qualname__", str(handler))

            try:
                # Support both sync and async handlers
                if inspect.iscoroutinefunction(handler):
                    handler_result = await handler(ctx)
                else:
                    # Run sync handler in executor to avoid blocking
                    loop = asyncio.get_running_loop()
                    handler_result = await loop.run_in_executor(
                        None, handler, ctx
                    )

                result.results.append(
                    HandlerResult(
                        handler_name=handler_name,
                        plugin=hook.plugin,
                        success=True,
                        result=handler_result,
                    )
                )
                logger.debug(
                    "Handler %s for '%s' succeeded (plugin=%s)",
                    handler_name,
                    event,
                    hook.plugin or "core",
                )

            except Exception as exc:
                error_msg = f"{type(exc).__name__}: {exc}"
                result.results.append(
                    HandlerResult(
                        handler_name=handler_name,
                        plugin=hook.plugin,
                        success=False,
                        error=error_msg,
                    )
                )
                logger.error(
                    "Handler %s for '%s' failed: %s (plugin=%s)",
                    handler_name,
                    event,
                    error_msg,
                    hook.plugin or "core",
                    exc_info=True,
                )

        if result.all_succeeded:
            logger.debug("Event '%s' completed: all %d handlers succeeded", event, len(hooks))
        else:
            failed = sum(1 for r in result.results if not r.success)
            logger.warning(
                "Event '%s' completed: %d/%d handlers failed",
                event,
                failed,
                len(hooks),
            )

        return result

    async def dispatch_before(
        self,
        action: str,
        model_name: str,
        *,
        data: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> EventResult:
        """Convenience: fire a ``before_*`` lifecycle event.

        If any handler raises an exception, it propagates — allowing
        ``before_*`` hooks to reject operations (e.g. validation).

        Args:
            action: The lifecycle action (e.g. ``"create"``, ``"update"``).
            model_name: The model name (e.g. ``"Customer"``).
            data: The data being processed.
            metadata: Additional context.

        Returns:
            An ``EventResult``.

        Raises:
            Exception: If any ``before_*`` handler raises.
        """
        event = f"before_{action}:{model_name}"
        return await self.dispatch(event, data=data, metadata=metadata)

    async def dispatch_after(
        self,
        action: str,
        model_name: str,
        *,
        data: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> EventResult:
        """Convenience: fire an ``after_*`` lifecycle event.

        ``after_*`` events are fire-and-forget — errors are logged
        but never propagated.

        Args:
            action: The lifecycle action (e.g. ``"create"``, ``"update"``).
            model_name: The model name.
            data: The completed data.
            metadata: Additional context.

        Returns:
            An ``EventResult``.
        """
        event = f"after_{action}:{model_name}"
        return await self.dispatch(event, data=data, metadata=metadata)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

# Lazily initialised by the app lifespan after registry is ready.
_dispatcher: EventDispatcher | None = None


def get_dispatcher() -> EventDispatcher:
    """Return the global event dispatcher singleton.

    Raises:
        RuntimeError: If the dispatcher hasn't been initialised yet.
    """
    if _dispatcher is None:
        raise RuntimeError(
            "Event dispatcher not initialised. This happens automatically "
            "during app startup."
        )
    return _dispatcher


def init_dispatcher(registry: PravaahRegistry) -> EventDispatcher:
    """Initialise the global event dispatcher.

    Called once during app startup after the registry is populated.

    Args:
        registry: The framework's central registry.

    Returns:
        The initialised ``EventDispatcher``.
    """
    global _dispatcher  # noqa: PLW0603
    _dispatcher = EventDispatcher(registry)
    logger.info("Event dispatcher initialised")
    return _dispatcher
