# Event System

The Event System is the automation backbone of Pravaah.

It enables applications to react to business events without tightly coupling components together.

Instead of embedding business logic directly inside API routes or database operations, Pravaah uses events and hooks to orchestrate workflows.

This creates a flexible and scalable architecture where actions naturally flow from one event to another.

---

## Why Events?

In traditional applications, business logic often becomes tightly coupled to CRUD operations.

Example:

```text
Create Customer
      ↓
Save Record
      ↓
Generate Lead Score
      ↓
Send Notification
      ↓
Create Audit Log
```

All of this logic may live inside a single endpoint.

As applications grow, this approach becomes difficult to maintain.

The Event System separates these concerns.

---

## Event-Driven Architecture

Pravaah follows an event-driven model.

```text
Action Occurs
      ↓
Event Generated
      ↓
Hooks Triggered
      ↓
Workflow Executed
      ↓
Response Produced
```

This design allows features to evolve independently.

---

## Core Concepts

### Event

An event represents something that happened within the system.

Examples:

```text
Customer Created
Deal Updated
Note Deleted
Activity Added
```

Events describe facts.

They do not contain business logic.

---

### Hook

A hook reacts to an event.

Example:

```python
@after_create("Customer")
async def score_new_lead(payload):
    ...
```

When a Customer is created, the hook executes automatically.

---

### Workflow

A workflow is a chain of actions triggered by events.

Example:

```text
Customer Created
       ↓
Lead Scoring
       ↓
Customer Updated
       ↓
Notification Sent
```

The Event System forms the foundation for workflow execution.

---

## Event Lifecycle

Every operation follows a predictable lifecycle.

```text
Request
   ↓
Validation
   ↓
Database Action
   ↓
Event Dispatch
   ↓
Hook Execution
   ↓
Response
```

This ensures consistency across the framework.

---

## Supported Events

Pravaah currently provides lifecycle events for CRUD operations.

### Create Events

```text
before_create
after_create
```

---

### Update Events

```text
before_update
after_update
```

---

### Delete Events

```text
before_delete
after_delete
```

---

## Create Flow Example

When a customer is created:

```text
POST /crm/customers
          ↓
Customer Saved
          ↓
after_create Event
          ↓
Lead Scoring Hook
          ↓
Customer Updated
```

The route remains simple while automation happens through events.

---

## Update Flow Example

When a deal is marked as won:

```text
PUT /crm/deals/1
         ↓
Status = Won
         ↓
after_update Event
         ↓
Hook Executed
         ↓
Activity Created
```

This workflow exists independently from the API endpoint.

---

## Hook Registration

Hooks are registered by plugins.

Example:

```python
@after_create("Customer")
async def score_new_lead(payload):
    pass
```

Example:

```python
@after_update("Deal")
async def log_won_deal(payload):
    pass
```

Once registered, hooks automatically participate in the event lifecycle.

---

## CRM Plugin Example

The CRM plugin demonstrates event-driven automation.

### Lead Scoring Workflow

```text
Customer Created
        ↓
after_create Event
        ↓
score_new_lead Hook
        ↓
AI Lead Score Assigned
```

---

### Deal Won Workflow

```text
Deal Updated
       ↓
Status Changed To Won
       ↓
after_update Event
       ↓
log_won_deal Hook
       ↓
Activity Created
```

This workflow was successfully demonstrated in the CRM example application.

---

## Event Dispatcher

The Event Dispatcher coordinates event processing.

Responsibilities:

* Event registration
* Event publication
* Hook discovery
* Hook execution
* Workflow coordination

Architecture:

```text
Event Generated
        ↓
Event Dispatcher
        ↓
Matching Hooks
        ↓
Execution
```

This keeps workflow execution centralized and predictable.

---

## Benefits

### Loose Coupling

Components communicate through events instead of direct dependencies.

---

### Extensibility

New automation can be added without modifying existing code.

---

### Maintainability

Business logic remains isolated and easier to understand.

---

### Scalability

Additional workflows can be introduced as applications grow.

---

### Reusability

Hooks can be reused across plugins and workflows.

---

## Event Flow Visualization

The following diagram illustrates a complete event-driven request.

```text
HTTP Request
       ↓
Router
       ↓
CRUD Engine
       ↓
Database Operation
       ↓
Event Created
       ↓
Event Dispatcher
       ↓
Hooks Executed
       ↓
AI Services (Optional)
       ↓
Response
```

This architecture allows automation to remain independent from API implementation.

---

## Relationship to Workflow Engines

The Event System serves as the foundation for future workflow orchestration capabilities.

Current state:

```text
Event
  ↓
Hook
  ↓
Action
```

Future state:

```text
Event
  ↓
Workflow Engine
  ↓
Multiple Steps
  ↓
Retries
  ↓
Scheduling
  ↓
State Management
```

This aligns with the long-term vision of Pravaah as a workflow-oriented backend framework.

---

## Future Enhancements

Planned improvements include:

* Workflow Definitions
* Scheduled Events
* Retry Policies
* Event Persistence
* Workflow State Tracking
* Temporal Integration Research
* Long-Running Workflows

These capabilities will build upon the existing Event System.

---

## Summary

The Event System enables Pravaah applications to evolve from simple CRUD APIs into intelligent workflow-driven systems.

By separating events from business logic, Pravaah provides a scalable foundation for automation, orchestration, and AI-powered workflows.

The Event System is a critical component of the framework's philosophy:

**Everything Flows.**
