# CRUD Engine

The CRUD Engine is one of the core productivity features of Pravaah.

It automatically generates production-ready REST APIs from registered models, eliminating repetitive boilerplate code and enabling developers to focus on business logic.

---

## Overview

Most backend applications require the same fundamental operations:

* Create
* Read
* Update
* Delete

Developers often spend significant time implementing identical CRUD endpoints across different projects.

Pravaah automates this process through its Dynamic CRUD Engine.

---

## What Is CRUD?

CRUD represents the four fundamental database operations:

| Operation | Description               |
| --------- | ------------------------- |
| Create    | Add a new record          |
| Read      | Retrieve existing records |
| Update    | Modify existing records   |
| Delete    | Remove records            |

These operations form the foundation of most business applications.

---

## Traditional Approach

Without automation, developers typically create:

```text
Model
Schema
Validation
Router
Database Queries
Error Handling
Pagination
Documentation
```

for every entity in the system.

This introduces:

* Boilerplate code
* Repetition
* Maintenance overhead
* Inconsistent APIs

---

## Pravaah Approach

With Pravaah, developers define a model once.

The framework automatically generates the API layer.

```python
register_model(Customer)
```

The CRUD Engine handles the rest.

---

## Generated Endpoints

For a Customer model:

```python
class Customer(Base):
    ...
```

Pravaah automatically generates:

```text
POST   /customers
GET    /customers
GET    /customers/{id}
PUT    /customers/{id}
DELETE /customers/{id}
```

No additional route implementation is required.

---

## CRUD Generation Flow

```text
Model Registered
        ↓
CRUD Engine
        ↓
Router Generated
        ↓
Endpoints Created
        ↓
OpenAPI Updated
        ↓
Ready For Use
```

---

## Automatic Features

The CRUD Engine provides more than endpoint generation.

### Validation

Incoming requests are validated automatically.

```text
Invalid Input
       ↓
Validation Error
       ↓
Structured Response
```

---

### Pagination

List endpoints include pagination support.

Example:

```text
GET /customers?page=1&page_size=20
```

Response:

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

---

### OpenAPI Documentation

Every generated endpoint automatically appears in:

```text
/docs
/redoc
```

This ensures documentation remains synchronized with the implementation.

---

### Error Handling

The CRUD Engine includes standardized error handling.

Examples:

```text
404 Not Found
422 Validation Error
500 Internal Server Error
```

Responses follow a consistent structure throughout the application.

---

## Example: CRM Plugin

The CRM plugin demonstrates CRUD generation in practice.

### Customer

Generated Endpoints:

```text
POST   /crm/customers
GET    /crm/customers
GET    /crm/customers/{id}
PUT    /crm/customers/{id}
DELETE /crm/customers/{id}
```

---

### Deal

Generated Endpoints:

```text
POST   /crm/deals
GET    /crm/deals
GET    /crm/deals/{id}
PUT    /crm/deals/{id}
DELETE /crm/deals/{id}
```

---

### Activity

Generated Endpoints:

```text
POST   /crm/activities
GET    /crm/activities
GET    /crm/activities/{id}
PUT    /crm/activities/{id}
DELETE /crm/activities/{id}
```

---

## Integration with Events

The CRUD Engine integrates directly with the Event System.

Example:

```text
POST Customer
        ↓
Customer Created
        ↓
after_create Event
        ↓
Hook Execution
```

This enables automation without additional endpoint code.

---

## Integration with AI

Generated CRUD endpoints can trigger AI workflows.

Example:

```text
Customer Created
        ↓
after_create Hook
        ↓
AI Lead Scoring
        ↓
Customer Updated
```

This demonstrates how CRUD operations become part of larger workflows.

---

## Request Lifecycle

The following diagram illustrates a typical CRUD request.

```text
HTTP Request
       ↓
Router
       ↓
Validation
       ↓
CRUD Engine
       ↓
Database
       ↓
Event Dispatch
       ↓
Hooks
       ↓
Response
```

---

## Benefits

### Faster Development

Developers spend less time writing repetitive code.

---

### Consistency

Every generated API follows the same conventions.

---

### Maintainability

Changes to CRUD behavior can be made centrally.

---

### Scalability

New entities can be added rapidly.

---

### Documentation

OpenAPI documentation is generated automatically.

---

## Design Goals

The CRUD Engine was designed to provide:

* Minimal boilerplate
* Rapid development
* Consistent APIs
* Built-in validation
* Event integration
* Workflow compatibility

These goals enable developers to focus on business capabilities rather than infrastructure code.

---

## Future Enhancements

Planned improvements include:

* Advanced Filtering
* Sorting
* Bulk Operations
* Soft Deletes
* Audit Trails
* Field-Level Permissions
* GraphQL Support

---

## Summary

The CRUD Engine transforms model definitions into fully functional REST APIs.

By automating repetitive development tasks, Pravaah enables teams to build applications faster while maintaining consistency and quality.

The CRUD Engine is a foundational building block that powers plugins, workflows, events, and AI-driven automation throughout the framework.

**Everything Flows.**
