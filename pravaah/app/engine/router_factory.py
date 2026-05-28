"""Auto-generate FastAPI routers from registered models.

The router factory is the glue between the CRUD repository and the
REST API surface.  Call ``create_crud_router()`` with a model and its
Pydantic schemas, and you get a fully functional CRUD router with:

    POST   /           -> create
    GET    /           -> list (paginated)
    GET    /{id}       -> read one
    PUT    /{id}       -> update
    DELETE /{id}       -> delete

Architecture Notes:
    - Each generated router is self-contained with its own ``CRUDBase``
      instance created per-request via the ``get_db`` dependency.
    - Response models are explicitly set so OpenAPI docs show the exact
      schema for each endpoint.
    - The factory supports an optional ``auth_dependency`` for per-router
      authentication requirements.
    - The ``PaginatedResponse`` wrapper provides consistent pagination
      metadata across all list endpoints.

Scalability:
    - Adding a new model to the framework is a two-line operation:
      define the model + schemas, call ``create_crud_router()``.
    - Plugins use this via the registry:  the app lifespan can
      auto-generate routers for all registered models.
    - Custom endpoints can coexist with auto-generated ones — just
      add them to the same router or register a separate one.

Common Pitfalls:
    - Don't forget to set ``model_config = ConfigDict(from_attributes=True)``
      on your read schema — without it, Pydantic can't serialise
      SQLAlchemy model instances.
    - The ``id`` path parameter is typed as ``int`` by default.
      Override ``pk_type`` if your model uses UUID or string PKs.
"""
# NOTE: Do NOT use `from __future__ import annotations` in this file.
# FastAPI inspects type annotations at runtime for dependency injection
# and request body parsing.  PEP 563 deferred annotations would turn
# the closure-captured schema types into unresolvable strings.

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from pravaah.app.core.database import get_db
from pravaah.app.core.exceptions import NotFoundError
from pravaah.app.engine.crud import CRUDBase
from pravaah.app.engine.pagination import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    PaginatedResponse,
)

logger = logging.getLogger("pravaah.engine.router_factory")


def create_crud_router(
    *,
    name: str,
    model: type,
    create_schema: type,
    update_schema: type,
    read_schema: type,
    prefix: str | None = None,
    tags: list[str] | None = None,
    pk_type: type = int,
    auth_dependency: Any | None = None,
) -> APIRouter:
    """Generate a full CRUD router for a model.

    Creates five endpoints (create, list, read, update, delete) wired
    to a ``CRUDBase`` repository.

    Args:
        name: Human-readable model name (e.g. ``"Customer"``).
              Used in OpenAPI summaries and error messages.
        model: The SQLAlchemy model class.
        create_schema: Pydantic schema for POST payloads.
        update_schema: Pydantic schema for PUT payloads.
        read_schema: Pydantic schema for GET responses.
        prefix: URL prefix (default: ``/name_lowercase_plural``).
        tags: OpenAPI tags (default: ``[name]``).
        pk_type: Type of the primary key (default ``int``).
        auth_dependency: Optional FastAPI dependency for authentication.

    Returns:
        A configured ``APIRouter`` with all CRUD endpoints.
    """
    # Derive defaults
    if prefix is None:
        prefix = f"/{name.lower()}s"
    if tags is None:
        tags = [name]

    # Router dependencies (e.g., auth)
    dependencies = []
    if auth_dependency is not None:
        dependencies.append(Depends(auth_dependency))

    router = APIRouter(prefix=prefix, tags=tags, dependencies=dependencies)

    # ---- CREATE -------------------------------------------------------
    @router.post(
        "/",
        response_model=read_schema,
        status_code=201,
        summary=f"Create {name}",
        description=f"Create a new {name} record.",
    )
    async def create_record(
        payload: create_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        crud = CRUDBase(model, db)
        return await crud.create(payload)

    # ---- LIST (paginated) ---------------------------------------------
    @router.get(
        "/",
        response_model=PaginatedResponse[read_schema],  # type: ignore[valid-type]
        summary=f"List {name}s",
        description=f"Retrieve a paginated list of {name} records.",
    )
    async def list_records(
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(
            default=DEFAULT_PAGE_SIZE,
            ge=1,
            le=MAX_PAGE_SIZE,
            description=f"Items per page (max {MAX_PAGE_SIZE})",
        ),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        crud = CRUDBase(model, db)
        offset = (page - 1) * page_size

        items = await crud.get_multi(offset=offset, limit=page_size)
        total = await crud.count()

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ---- READ ONE -----------------------------------------------------
    @router.get(
        "/{record_id}",
        response_model=read_schema,
        summary=f"Get {name}",
        description=f"Retrieve a single {name} by ID.",
    )
    async def get_record(
        record_id: pk_type,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        crud = CRUDBase(model, db)
        record = await crud.get(record_id)
        if record is None:
            raise NotFoundError(
                f"{name} with id '{record_id}' not found",
                error_code=f"{name.upper()}_NOT_FOUND",
            )
        return record

    # ---- UPDATE -------------------------------------------------------
    @router.put(
        "/{record_id}",
        response_model=read_schema,
        summary=f"Update {name}",
        description=f"Update an existing {name} record. Only provided fields are changed.",
    )
    async def update_record(
        record_id: pk_type,  # type: ignore[valid-type]
        payload: update_schema,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        crud = CRUDBase(model, db)
        record = await crud.update(record_id, payload)
        if record is None:
            raise NotFoundError(
                f"{name} with id '{record_id}' not found",
                error_code=f"{name.upper()}_NOT_FOUND",
            )
        return record

    # ---- DELETE -------------------------------------------------------
    @router.delete(
        "/{record_id}",
        status_code=200,
        summary=f"Delete {name}",
        description=f"Delete a {name} record by ID.",
    )
    async def delete_record(
        record_id: pk_type,  # type: ignore[valid-type]
        db: AsyncSession = Depends(get_db),
    ) -> dict[str, Any]:
        crud = CRUDBase(model, db)
        deleted = await crud.delete(record_id)
        if not deleted:
            raise NotFoundError(
                f"{name} with id '{record_id}' not found",
                error_code=f"{name.upper()}_NOT_FOUND",
            )
        return {"deleted": True, "id": record_id}

    logger.debug(
        "CRUD router created: %s (%s) with %d endpoints",
        name,
        prefix,
        5,
    )
    return router
