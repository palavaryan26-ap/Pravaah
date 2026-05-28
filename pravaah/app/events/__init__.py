"""Pravaah event system.

Provides event-driven hooks for CRUD lifecycle events and custom events.

Public API::

    from pravaah.app.events import (
        EventDispatcher, EventContext, EventResult,
        get_dispatcher, init_dispatcher,
        on_event, before_create, after_create,
        before_update, after_update, before_delete, after_delete,
        collect_hooks,
    )
"""
from __future__ import annotations

from pravaah.app.events.decorators import (
    after_create,
    after_delete,
    after_update,
    before_create,
    before_delete,
    before_update,
    collect_hooks,
    on_event,
)
from pravaah.app.events.dispatcher import (
    EventContext,
    EventDispatcher,
    EventResult,
    get_dispatcher,
    init_dispatcher,
)

__all__ = [
    "EventContext",
    "EventDispatcher",
    "EventResult",
    "after_create",
    "after_delete",
    "after_update",
    "before_create",
    "before_delete",
    "before_update",
    "collect_hooks",
    "get_dispatcher",
    "init_dispatcher",
    "on_event",
]
