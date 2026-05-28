"""Pravaah CRUD and routing engine.

The engine provides auto-generated REST APIs from SQLAlchemy models
and Pydantic schemas.

Public API::

    from pravaah.app.engine import CRUDBase, create_crud_router, PaginatedResponse
"""
from __future__ import annotations

from pravaah.app.engine.crud import CRUDBase
from pravaah.app.engine.pagination import PaginatedResponse, PaginationParams
from pravaah.app.engine.router_factory import create_crud_router

__all__ = [
    "CRUDBase",
    "PaginatedResponse",
    "PaginationParams",
    "create_crud_router",
]
