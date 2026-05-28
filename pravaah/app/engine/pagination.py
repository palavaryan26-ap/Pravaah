"""Reusable pagination schema and FastAPI dependency.

Provides a standardized pagination interface used by the CRUD engine
and any custom endpoints that need paginated responses.

Architecture Notes:
    - ``PaginationParams`` is a FastAPI dependency — inject it into
      any route via ``Depends(PaginationParams)``.
    - ``PaginatedResponse`` is a generic Pydantic model that wraps
      any list of items with pagination metadata.
    - ``page`` is 1-indexed (user-friendly), internally converted to
      ``offset`` for SQL queries.
    - ``page_size`` is capped at ``MAX_PAGE_SIZE`` to prevent clients
      from requesting absurdly large result sets.

Scalability:
    - The pagination contract is stable — changing the underlying query
      engine (SQL, Elasticsearch, etc.) doesn't affect the API shape.
    - ``PaginatedResponse`` is generic over ``T``, so OpenAPI docs
      show the correct item schema for each model.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

# Hard ceiling to prevent abuse
MAX_PAGE_SIZE: int = 100
DEFAULT_PAGE_SIZE: int = 20


class PaginationParams:
    """FastAPI dependency for pagination query parameters.

    Usage::

        @router.get("/items")
        async def list_items(pagination: PaginationParams = Depends()):
            offset = pagination.offset
            limit = pagination.limit

    Attributes:
        page: Current page number (1-indexed, default 1).
        page_size: Number of items per page (default 20, max 100).
        offset: Calculated SQL offset (``(page - 1) * page_size``).
        limit: Same as ``page_size`` — alias for SQL clarity.
    """

    def __init__(
        self,
        page: int = Field(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Field(
            default=DEFAULT_PAGE_SIZE,
            ge=1,
            le=MAX_PAGE_SIZE,
            description=f"Items per page (max {MAX_PAGE_SIZE})",
        ),
    ) -> None:
        self.page = page
        self.page_size = min(page_size, MAX_PAGE_SIZE)
        self.offset = (self.page - 1) * self.page_size
        self.limit = self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response envelope.

    Wraps a list of items with pagination metadata so clients can
    implement cursor/offset pagination consistently.

    Attributes:
        items: The page of results.
        total: Total number of records matching the query.
        page: Current page number.
        page_size: Number of items per page.
        total_pages: Total number of pages.
    """

    items: list[T]
    total: int = Field(ge=0, description="Total matching records")
    page: int = Field(ge=1, description="Current page")
    page_size: int = Field(ge=1, description="Items per page")
    total_pages: int = Field(ge=0, description="Total pages")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[T]:
        """Factory method to build a paginated response.

        Calculates ``total_pages`` automatically.

        Args:
            items: The items for the current page.
            total: Total number of matching records.
            page: Current page number.
            page_size: Items per page.

        Returns:
            A fully populated ``PaginatedResponse``.
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
