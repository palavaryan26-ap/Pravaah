"""Note plugin — verifies the CRUD engine end-to-end.

Registers a ``Note`` model with auto-generated CRUD endpoints.
This plugin will be removed once the CRM demo is built (Phase 7).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from pravaah.app.core.database import Base, TimestampMixin
from pravaah.app.engine import create_crud_router
from pravaah.app.plugins.base import PravaahPlugin
from pravaah.app.plugins.manifest import PluginManifest


# ---------------------------------------------------------------------------
# SQLAlchemy model
# ---------------------------------------------------------------------------


class Note(Base, TimestampMixin):
    """A simple note — used to verify the CRUD engine."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class NoteCreate(BaseModel):
    """Schema for creating a note."""

    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    content: str = Field(default="", description="Note body")
    status: str = Field(default="draft", description="Note status")


class NoteUpdate(BaseModel):
    """Schema for updating a note (partial updates supported)."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    status: str | None = None


class NoteRead(BaseModel):
    """Schema for reading a note."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------


class NotePlugin(PravaahPlugin):
    """Plugin that demonstrates the CRUD engine with a Note model."""

    manifest = PluginManifest(
        name="notes",
        version="0.1.0",
        description="Note management - CRUD engine verification plugin",
        author="Pravaah Team",
    )

    def setup(self, app, registry):
        """Register the Note model, CRUD routes, and event hooks."""
        # Register model in the framework registry
        self.register_model(
            "Note", Note, NoteCreate, NoteUpdate, NoteRead,
        )

        # Auto-generate CRUD router
        note_router = create_crud_router(
            name="Note",
            model=Note,
            create_schema=NoteCreate,
            update_schema=NoteUpdate,
            read_schema=NoteRead,
            prefix="/notes",
            tags=["Notes"],
        )
        self.register_routes(note_router)

        # Register event hooks
        from pravaah.app.events.decorators import collect_hooks
        from pravaah.plugins.notes import hooks

        for event, handler, priority in collect_hooks(hooks):
            self.register_hook(event, handler, priority=priority)
