"""Pravaah plugin: crm."""
from __future__ import annotations

from pravaah.app.engine import create_crud_router
from pravaah.app.events.decorators import collect_hooks
from pravaah.app.plugins.base import PravaahPlugin
from pravaah.app.plugins.manifest import PluginManifest


class CrmPlugin(PravaahPlugin):
    """The crm plugin."""

    manifest = PluginManifest(
        name="crm",
        version="0.1.0",
        description="Pravaah CRM Demo Plugin",
        author="Pravaah Team",
    )

    def setup(self, app, registry):
        """Register models, routes, and hooks."""
        from pravaah.plugins.crm import api, hooks
        from pravaah.plugins.crm.models import Activity, Customer, Deal
        from pravaah.plugins.crm.schemas import (
            ActivityCreate,
            ActivityRead,
            ActivityUpdate,
            CustomerCreate,
            CustomerRead,
            CustomerUpdate,
            DealCreate,
            DealRead,
            DealUpdate,
        )

        # 1. Register Models
        self.register_model("Customer", Customer, CustomerCreate, CustomerUpdate, CustomerRead)
        self.register_model("Deal", Deal, DealCreate, DealUpdate, DealRead)
        self.register_model("Activity", Activity, ActivityCreate, ActivityUpdate, ActivityRead)

        # 2. Auto-generate CRUD routers
        customer_router = create_crud_router(
            name="Customer",
            model=Customer,
            create_schema=CustomerCreate,
            update_schema=CustomerUpdate,
            read_schema=CustomerRead,
            prefix="/crm/customers",
            tags=["CRM - Customers"],
        )
        deal_router = create_crud_router(
            name="Deal",
            model=Deal,
            create_schema=DealCreate,
            update_schema=DealUpdate,
            read_schema=DealRead,
            prefix="/crm/deals",
            tags=["CRM - Deals"],
        )
        activity_router = create_crud_router(
            name="Activity",
            model=Activity,
            create_schema=ActivityCreate,
            update_schema=ActivityUpdate,
            read_schema=ActivityRead,
            prefix="/crm/activities",
            tags=["CRM - Activities"],
        )
        
        # 3. Register all routes
        self.register_routes(customer_router)
        self.register_routes(deal_router)
        self.register_routes(activity_router)
        self.register_routes(api.router)

        # 4. Register event hooks
        for event, handler, priority in collect_hooks(hooks):
            self.register_hook(event, handler, priority=priority)
