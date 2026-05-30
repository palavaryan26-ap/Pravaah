# Plugin System

The Plugin System is the foundation of Pravaah.

Rather than building applications as a collection of tightly coupled modules, Pravaah encourages developers to build self-contained plugins that can register functionality with the framework.

This approach enables modularity, extensibility, and long-term maintainability.

---

## What Is a Plugin?

A plugin is a self-contained package that extends the framework.

A plugin can contribute:

* Models
* Routes
* Services
* Event Hooks
* Workflows
* Configuration

Plugins allow features to be developed independently while still integrating seamlessly into the framework.

---

## Why Plugins?

Traditional applications often become difficult to maintain as they grow.

Features become tightly coupled.

Dependencies spread across the codebase.

Business logic becomes difficult to isolate.

Pravaah addresses these challenges through a plugin-driven architecture.

Benefits include:

* Separation of concerns
* Reusability
* Easier maintenance
* Improved testing
* Faster development

---

## Plugin Lifecycle

Every plugin follows a standard lifecycle.

```text id="f2yyrj"
Discovery
    ↓
Loading
    ↓
Setup
    ↓
Registration
    ↓
Ready
```

### Discovery

The framework scans configured plugin directories.

Each plugin is identified and validated.

---

### Loading

Plugin code is imported into the application.

Metadata is collected.

Dependencies are resolved.

---

### Setup

The framework executes the plugin's setup process.

During setup, the plugin may register:

* Models
* Services
* Routes
* Hooks

---

### Registration

Framework components are registered in the central registry.

The plugin becomes available to the rest of the application.

---

### Ready

The plugin is fully operational.

Routes become accessible.

Events can be handled.

Services become available.

---

## Plugin Structure

A typical plugin may look like:

```text id="m09nk9"
crm/
│
├── plugin.py
├── models.py
├── schemas.py
├── routes.py
├── hooks.py
└── services.py
```

This structure keeps functionality organized and maintainable.

---

## Example Plugin

```python id="p66n2m"
class CRMPlugin(PravaahPlugin):
    name = "crm"
    version = "0.1.0"

    async def setup(self):
        pass
```

During setup, the plugin can register framework resources.

---

## Registering Models

Plugins can contribute database models.

Example:

```python id="7dnxrb"
registry.register_model(Customer)
registry.register_model(Deal)
registry.register_model(Activity)
```

Once registered, these models become available to the CRUD engine and event system.

---

## Registering Routes

Plugins can expose API endpoints.

Example:

```python id="ijr0n8"
registry.register_router(customer_router)
```

These routes are automatically mounted during application startup.

---

## Registering Services

Services provide reusable business functionality.

Example:

```python id="f4h43j"
registry.register_service("ai", ai_service)
```

Services can then be used throughout the framework.

---

## Registering Hooks

Plugins can react to events through hooks.

Example:

```python id="95hf4e"
@after_create("Customer")
async def score_new_lead(payload):
    ...
```

When a customer is created:

```text id="1x3m5v"
Customer Created
       ↓
after_create Event
       ↓
Hook Executed
       ↓
Lead Score Assigned
```

---

## CRM Plugin Walkthrough

The CRM plugin included with Pravaah demonstrates the plugin system in action.

### Registered Models

```text id="bhsd0o"
Customer
Deal
Activity
```

### Registered Routes

```text id="k0hq7q"
/crm/customers
/crm/deals
/crm/activities
```

### Registered Hooks

```text id="am1w8w"
after_create(Customer)

after_update(Deal)
```

### Registered Workflows

```text id="qv5e25"
Lead Scoring

Deal Won Automation

AI Email Drafting
```

---

## Plugin Isolation

Each plugin operates independently.

This means:

* Models remain organized
* Business logic stays local
* Features can evolve separately
* Testing becomes simpler

A failure in one plugin should not affect unrelated plugins.

---

## Plugin Communication

Plugins communicate through:

```text id="5qj7gk"
Registry
Events
Services
```

rather than direct dependencies.

This reduces coupling and improves maintainability.

---

## Design Goals

The Plugin System is designed to provide:

* Extensibility
* Modularity
* Scalability
* Maintainability
* Rapid Development

It enables Pravaah to grow from a simple backend framework into a platform capable of supporting complex enterprise applications.

---

## Future Enhancements

Planned improvements include:

* Plugin Dependency Management
* Plugin Marketplace
* Dynamic Plugin Loading
* Plugin Versioning
* Workflow Plugins

These capabilities will further strengthen the ecosystem around Pravaah.

## Summary

Plugins are the building blocks of Pravaah.

Every feature, workflow, and business capability can be packaged as a plugin and integrated into the framework.

This modular approach is one of the key principles behind the Pravaah architecture.

**Everything Flows.**
