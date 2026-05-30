# Architecture

## Architecture Overview

![Pravaah Architecture](/img/pravaah-architecture.png)

Pravaah is an AI-native, flow-oriented backend framework designed around modularity, automation, and workflow-driven application development.

Instead of treating applications as isolated endpoints and services, Pravaah models business processes as interconnected flows powered by events, hooks, plugins, and intelligent actions.

## Architectural Philosophy

### Everything Flows

Traditional backend systems are often built as disconnected APIs.

Pravaah approaches application development differently.

Every operation generates events.

Events trigger workflows.

Workflows execute business actions.

This creates a natural flow of business logic throughout the system.

## High-Level Architecture

```text
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ CRUD Engine │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Event Layer │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Hooks    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Services   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Response   │
└─────────────┘
```

## Core Components

### Application Layer

The application layer initializes and coordinates the framework.

Responsibilities:

* Configuration loading
* Database initialization
* Plugin discovery
* Service registration
* Event system startup

---

### Registry

The Registry acts as the central dependency container.

It stores:

* Models
* Services
* Routers
* Hooks
* Plugins

The Registry allows framework components to discover and communicate with one another without tight coupling.

---

### Plugin Loader

The Plugin Loader discovers and loads plugins automatically.

Plugin lifecycle:

```text
Discover
   ↓
Load
   ↓
Setup
   ↓
Register
   ↓
Ready
```

Each plugin can contribute:

* Models
* Routes
* Services
* Event hooks
* Custom functionality

---

### CRUD Engine

The CRUD Engine automatically generates REST APIs from model definitions.

Example:

```python
register_crud(Customer)
```

Generated endpoints:

```text
POST   /customers
GET    /customers
GET    /customers/{id}
PUT    /customers/{id}
DELETE /customers/{id}
```

Benefits:

* Reduced boilerplate
* Consistent API design
* Faster development

---

### Event Dispatcher

The Event Dispatcher coordinates workflow execution.

Supported lifecycle events:

```text
before_create
after_create

before_update
after_update

before_delete
after_delete
```

These events enable automation without modifying core business logic.

---

### Hook System

Hooks allow plugins to react to events.

Example:

```python
@after_create("Customer")
async def score_new_lead(payload):
    ...
```

When a Customer is created:

```text
Customer Created
        ↓
after_create Event
        ↓
Hook Execution
        ↓
Lead Score Generated
```

---

### AI Service Layer

Pravaah provides a provider-agnostic AI abstraction layer.

Capabilities include:

* Lead scoring
* Email drafting
* Content generation
* Intelligent automation

Architecture:

```text
Application
      ↓
AI Service
      ↓
Provider
      ↓
Response
```

This design allows different AI providers to be integrated without changing application code.

---

## Request Lifecycle

The following diagram shows a typical request flowing through the framework.

```text
HTTP Request
      ↓
Router
      ↓
CRUD Engine
      ↓
Database Operation
      ↓
Event Dispatch
      ↓
Hook Execution
      ↓
AI Service (Optional)
      ↓
Response
```

---

## CRM Plugin Example

The CRM plugin demonstrates the architecture in action.

### Customer Creation Flow

```text
Create Customer
        ↓
CRUD Engine
        ↓
Customer Stored
        ↓
after_create Event
        ↓
Lead Scoring Hook
        ↓
Customer Updated
```

### Deal Won Flow

```text
Deal Updated
        ↓
Status = Won
        ↓
after_update Event
        ↓
Workflow Hook
        ↓
Activity Created
```

### Email Drafting Flow

```text
API Request
        ↓
CRM Route
        ↓
AI Service
        ↓
Generated Email
        ↓
Response
```

---

## Design Goals

Pravaah is designed to provide:

* High extensibility
* Minimal boilerplate
* Workflow-oriented architecture
* AI-native capabilities
* Plugin-based modularity
* Production-ready deployment

## Looking Forward

The current architecture establishes the foundation for future workflow orchestration capabilities inspired by modern workflow engines.

Future enhancements include:

* Workflow definitions
* Long-running workflows
* Scheduling
* Retry policies
* Workflow state management

These capabilities will further strengthen Pravaah's vision of flow-oriented application development.

**Everything Flows.**

