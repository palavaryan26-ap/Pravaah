"""CRM database models.

Defines the core domain entities: Customer, Deal, and Activity.
Demonstrates relationships and schema design in Pravaah.
"""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pravaah.app.core.database import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    """A business prospect or client."""

    __tablename__ = "crm_customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    ai_lead_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    deals: Mapped[list["Deal"]] = relationship(
        "Deal", back_populates="customer", cascade="all, delete-orphan"
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="customer", cascade="all, delete-orphan"
    )


class Deal(Base, TimestampMixin):
    """A sales opportunity associated with a customer."""

    __tablename__ = "crm_deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="prospect")
    
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    customer: Mapped["Customer"] = relationship("Customer", back_populates="deals")


class Activity(Base, TimestampMixin):
    """A logged interaction or automated event."""

    __tablename__ = "crm_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # email, call, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("crm_customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    customer: Mapped["Customer"] = relationship("Customer", back_populates="activities")
