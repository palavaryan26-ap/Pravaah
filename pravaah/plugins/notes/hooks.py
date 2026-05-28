"""Event hooks for the Notes plugin.

Demonstrates the event system with CRUD lifecycle hooks.
"""
from __future__ import annotations

import logging

from pravaah.app.events.decorators import after_create, after_delete, after_update

logger = logging.getLogger("pravaah.plugins.notes.hooks")


@after_create("Note")
async def on_note_created(ctx):
    """Log when a note is created."""
    note_id = getattr(ctx.data, "id", "?")
    title = getattr(ctx.data, "title", "?")
    logger.info("[Hook] Note created: id=%s, title='%s'", note_id, title)
    return {"handled": True, "action": "note_created"}


@after_update("Note")
async def on_note_updated(ctx):
    """Log when a note is updated."""
    note_id = getattr(ctx.data, "id", "?")
    logger.info("[Hook] Note updated: id=%s", note_id)
    return {"handled": True, "action": "note_updated"}


@after_delete("Note")
async def on_note_deleted(ctx):
    """Log when a note is deleted."""
    note_id = ctx.data.get("id", "?") if isinstance(ctx.data, dict) else "?"
    logger.info("[Hook] Note deleted: id=%s", note_id)
    return {"handled": True, "action": "note_deleted"}
