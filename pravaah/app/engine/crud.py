"""Generic async CRUD repository.

``CRUDBase`` is a reusable, type-safe repository that provides
Create / Read / Update / Delete operations for any SQLAlchemy model
paired with Pydantic schemas.

Architecture Notes:
    - Uses Python generics (``ModelType``, ``CreateSchemaType``,
      ``UpdateSchemaType``) so every method is fully typed.
    - All operations use ``flush()`` instead of ``commit()`` — the
      ``get_db`` dependency handles transaction boundaries.  This
      lets service-layer code compose multiple CRUD operations in a
      single transaction.
    - ``get_multi`` supports offset/limit pagination and optional
      filtering via SQLAlchemy column expressions.
    - The repository is instantiated per-request with a session, keeping
      it stateless across requests.

Scalability:
    - Concrete repositories can subclass ``CRUDBase`` to add
      domain-specific queries (e.g. ``get_by_email``).
    - The generic pattern means the router factory can auto-create
      a ``CRUDBase`` instance for any registered model — zero
      boilerplate per model.
    - Future: add soft-delete support, audit trails, or caching
      as mixin behaviours without touching this base class.

Inspired by:
    - Framework-M's DocType controller hooks (before_save, after_save)
    - FastAPI CRUD patterns from the community
    - Django's Manager/QuerySet pattern (but async + explicit)
"""
from __future__ import annotations

import logging
from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("pravaah.engine.crud")


def _get_dispatcher():
    """Lazy import to avoid circular dependency at module load."""
    try:
        from pravaah.app.events.dispatcher import get_dispatcher
        return get_dispatcher()
    except (ImportError, RuntimeError):
        return None

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic async CRUD repository for SQLAlchemy models.

    Provides standard database operations with proper error handling
    and transaction semantics.

    Usage::

        # Direct instantiation
        repo = CRUDBase(Customer, db_session)
        customer = await repo.create(CustomerCreate(name="Alice"))

        # Or subclass for custom queries
        class CustomerRepository(CRUDBase[Customer, CustomerCreate, CustomerUpdate]):
            async def get_by_email(self, email: str) -> Customer | None:
                result = await self.session.execute(
                    select(self.model).where(self.model.email == email)
                )
                return result.scalar_one_or_none()

    Args:
        model: The SQLAlchemy model class.
        session: An ``AsyncSession`` for database operations.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, schema: CreateSchemaType) -> ModelType:
        """Create a new record.

        Fires ``before_create:ModelName`` and ``after_create:ModelName``
        events if the event dispatcher is available.

        Args:
            schema: Pydantic schema with the creation data.

        Returns:
            The newly created model instance with generated fields
            (id, timestamps) populated.
        """
        model_name = self.model.__name__
        data = schema.model_dump()

        # Fire before_create event
        dispatcher = _get_dispatcher()
        if dispatcher:
            await dispatcher.dispatch_before("create", model_name, data=data)

        db_obj = self.model(**data)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        logger.debug("Created %s(id=%s)", model_name, getattr(db_obj, "id", "?"))

        # Fire after_create event
        if dispatcher:
            await dispatcher.dispatch_after("create", model_name, data=db_obj)

        return db_obj

    async def get(self, record_id: Any) -> ModelType | None:
        """Retrieve a single record by primary key.

        Args:
            record_id: The primary key value.

        Returns:
            The model instance, or ``None`` if not found.
        """
        return await self.session.get(self.model, record_id)

    async def get_multi(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: list[Any] | None = None,
        order_by: Any | None = None,
    ) -> Sequence[ModelType]:
        """Retrieve multiple records with pagination and optional filtering.

        Args:
            offset: Number of records to skip.
            limit: Maximum number of records to return.
            filters: Optional list of SQLAlchemy filter expressions
                     (e.g. ``[Customer.status == "active"]``).
            order_by: Optional SQLAlchemy order expression
                      (e.g. ``Customer.created_at.desc()``).

        Returns:
            A sequence of model instances.
        """
        stmt = select(self.model)

        if filters:
            for f in filters:
                stmt = stmt.where(f)

        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            # Default: order by primary key (usually 'id')
            pk = self._get_pk_column()
            if pk is not None:
                stmt = stmt.order_by(pk)

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: list[Any] | None = None) -> int:
        """Count records matching optional filters.

        Args:
            filters: Optional list of SQLAlchemy filter expressions.

        Returns:
            Total number of matching records.
        """
        stmt = select(func.count()).select_from(self.model)

        if filters:
            for f in filters:
                stmt = stmt.where(f)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update(
        self,
        record_id: Any,
        schema: UpdateSchemaType,
    ) -> ModelType | None:
        """Update an existing record.

        Fires ``before_update:ModelName`` and ``after_update:ModelName``
        events if the event dispatcher is available.

        Only fields present in the schema (non-default) are updated,
        thanks to ``model_dump(exclude_unset=True)``.

        Args:
            record_id: The primary key of the record to update.
            schema: Pydantic schema with the update data.

        Returns:
            The updated model instance, or ``None`` if not found.
        """
        db_obj = await self.get(record_id)
        if db_obj is None:
            return None

        model_name = self.model.__name__
        update_data = schema.model_dump(exclude_unset=True)

        # Fire before_update event
        dispatcher = _get_dispatcher()
        if dispatcher:
            await dispatcher.dispatch_before(
                "update", model_name,
                data={"id": record_id, "changes": update_data},
            )

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await self.session.flush()
        await self.session.refresh(db_obj)
        logger.debug("Updated %s(id=%s)", model_name, record_id)

        # Fire after_update event
        if dispatcher:
            await dispatcher.dispatch_after("update", model_name, data=db_obj)

        return db_obj

    async def delete(self, record_id: Any) -> bool:
        """Delete a record by primary key.

        Fires ``before_delete:ModelName`` and ``after_delete:ModelName``
        events if the event dispatcher is available.

        Args:
            record_id: The primary key of the record to delete.

        Returns:
            ``True`` if the record was deleted, ``False`` if not found.
        """
        db_obj = await self.get(record_id)
        if db_obj is None:
            return False

        model_name = self.model.__name__

        # Fire before_delete event
        dispatcher = _get_dispatcher()
        if dispatcher:
            await dispatcher.dispatch_before(
                "delete", model_name,
                data={"id": record_id},
            )

        await self.session.delete(db_obj)
        await self.session.flush()
        logger.debug("Deleted %s(id=%s)", model_name, record_id)

        # Fire after_delete event
        if dispatcher:
            await dispatcher.dispatch_after(
                "delete", model_name,
                data={"id": record_id},
            )

        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_pk_column(self) -> Any | None:
        """Return the primary key column for default ordering."""
        try:
            mapper = self.model.__mapper__  # type: ignore[attr-defined]
            pk_cols = mapper.primary_key
            if pk_cols:
                return pk_cols[0]
        except AttributeError:
            pass
        return None
