"""CRM custom API endpoints.

Demonstrates adding custom routes alongside auto-generated CRUD endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from pravaah.app.core.database import get_db
from pravaah.app.core.registry import registry
from pravaah.plugins.crm.models import Customer

router = APIRouter(prefix="/crm/custom", tags=["CRM Custom"])


class DraftEmailResponse(BaseModel):
    subject: str
    body: str


@router.post(
    "/customers/{customer_id}/draft_email",
    response_model=DraftEmailResponse,
    summary="Draft AI Email",
)
async def draft_customer_email(
    customer_id: int,
    session: AsyncSession = Depends(get_db),
) -> DraftEmailResponse:
    """Use AI to draft a personalized email to a customer."""
    customer = await session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    ai = registry.get_service("ai")
    if not ai:
        raise HTTPException(
            status_code=503, detail="AI service disabled in config"
        )

    # Gather context
    context = (
        f"Customer Name: {customer.name}\n"
        f"Company: {customer.company}\n"
        f"Summary: {customer.summary or 'N/A'}\n"
    )

    # Ask AI to generate email
    schema = {
        "subject": "Email subject line",
        "body": "Full email body",
    }
    prompt = f"Draft a professional check-in email for this client:\n\n{context}"
    
    result = await ai.extract(prompt, schema=schema)
    
    return DraftEmailResponse(
        subject=result.get("subject", "Check-in from Pravaah"),
        body=result.get("body", "[Failed to generate email body]"),
    )
