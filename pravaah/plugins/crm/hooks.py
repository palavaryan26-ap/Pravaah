"""Event hooks for the CRM plugin.

Automates workflows using the Pravaah Event System and AI Layer.
"""
from __future__ import annotations

import logging
from sqlalchemy.orm import object_session

from pravaah.app.core.registry import registry
from pravaah.app.events.decorators import after_create, after_update
from pravaah.plugins.crm.models import Activity, Customer, Deal

logger = logging.getLogger("pravaah.plugins.crm.hooks")


@after_create("Customer")
async def score_new_lead(ctx):
    """Automatically score new customers using AI."""
    customer: Customer = ctx.data
    
    ai = registry.get_service("ai")
    if not ai:
        logger.warning("AI service unavailable, skipping lead scoring")
        return {"handled": False, "reason": "ai_disabled"}

    logger.info("Generating AI lead score for customer: %s", customer.name)
    
    # Use AI to evaluate the lead
    text = (
        f"Name: {customer.name}\n"
        f"Email: {customer.email}\n"
        f"Company: {customer.company}\n"
        "Evaluate this B2B software prospect."
    )
    schema = {
        "score": "Integer 0-100 indicating lead quality",
        "summary": "1 sentence explaining why",
    }
    
    result = await ai.extract(text, schema=schema)
    
    # Mutate the SQLAlchemy object (will be committed at end of request)
    score = result.get("score")
    if isinstance(score, int):
        customer.ai_lead_score = score
        customer.summary = result.get("summary")
        logger.info("Assigned lead score %d to %s", score, customer.name)
    
    return {"handled": True, "score": score}


@after_update("Deal")
async def log_won_deal(ctx):
    """Automatically create an Activity when a deal is won."""
    deal: Deal = ctx.data
    
    if deal.status == "won":
        session = object_session(deal)
        if session:
            logger.info("Deal %d won! Orchestrating activity...", deal.id)
            activity = Activity(
                type="system",
                content=f"Deal '{deal.title}' was won for ${deal.amount:,.2f}!",
                customer_id=deal.customer_id
            )
            session.add(activity)
            # No flush needed, the FastAPI dependency handles the transaction
            return {"handled": True, "action": "activity_created"}
    
    return {"handled": False}
