"""CRM Pydantic schemas.

Provides Create, Update, and Read schemas for Customer, Deal, and Activity.
These are used by the auto-generated CRUD engine.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Customer Schemas
# ---------------------------------------------------------------------------

class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    company: str = Field(..., min_length=2, max_length=100)
    status: str = Field(default="new")


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: str | None = Field(default=None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    company: str | None = Field(default=None, min_length=2, max_length=100)
    status: str | None = None
    ai_lead_score: int | None = Field(default=None, ge=0, le=100)
    summary: str | None = None


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    company: str
    status: str
    ai_lead_score: int
    summary: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Deal Schemas
# ---------------------------------------------------------------------------

class DealCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    amount: float = Field(default=0.0, ge=0.0)
    status: str = Field(default="prospect")
    customer_id: int


class DealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    amount: float | None = Field(default=None, ge=0.0)
    status: str | None = None


class DealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    amount: float
    status: str
    customer_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Activity Schemas
# ---------------------------------------------------------------------------

class ActivityCreate(BaseModel):
    type: str = Field(..., min_length=2, max_length=50)
    content: str = Field(..., min_length=1)
    customer_id: int


class ActivityUpdate(BaseModel):
    type: str | None = Field(default=None, min_length=2, max_length=50)
    content: str | None = Field(default=None, min_length=1)


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    content: str
    customer_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
