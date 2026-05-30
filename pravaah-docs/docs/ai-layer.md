# AI Layer

The AI Layer is one of the defining characteristics of Pravaah.

While most backend frameworks treat Artificial Intelligence as an external integration, Pravaah treats AI as a first-class framework capability.

The AI Layer enables developers to build intelligent workflows, automate business processes, and integrate AI-powered functionality without tightly coupling applications to a specific AI provider.

---

## Why an AI Layer?

Modern applications increasingly rely on AI capabilities.

Common use cases include:

* Lead Scoring
* Email Generation
* Content Creation
* Classification
* Summarization
* Workflow Automation
* Intelligent Recommendations

Without an abstraction layer, applications become tightly coupled to a single AI provider.

Pravaah solves this problem through a provider-agnostic AI architecture.

---

## Design Goals

The AI Layer was designed with the following goals:

### Provider Independence

Applications should not depend on a specific AI vendor.

---

### Reusability

AI capabilities should be reusable across plugins and workflows.

---

### Extensibility

New providers should be easy to integrate.

---

### Workflow Integration

AI should participate naturally within application workflows.

---

### Developer Simplicity

Developers should interact with a single interface regardless of the underlying provider.

---

## High-Level Architecture

```text
Application
      ↓
Plugin
      ↓
AI Service Layer
      ↓
AI Provider
      ↓
Response
```

The AI Layer acts as a bridge between business logic and external AI systems.

---

## Core Components

### AI Service

The AI Service provides a unified interface for AI operations.

Responsibilities:

* Request handling
* Provider abstraction
* Response normalization
* Error handling

Applications interact with the AI Service rather than directly with providers.

---

### AI Provider

Providers are responsible for executing AI operations.

Examples include:

```text
OpenAI
Anthropic
Google Gemini
Local Models
Mock Provider
```

Each provider implements a common contract.

---

### Registry Integration

The AI Service is registered with the framework registry.

Example:

```python
registry.register_service("ai", ai_service)
```

Plugins can access the service through the registry.

---

## AI Request Flow

The following diagram illustrates a typical AI operation.

```text
API Request
      ↓
Plugin
      ↓
AI Service
      ↓
Provider
      ↓
Generated Result
      ↓
Response
```

This architecture ensures a clean separation between business logic and AI implementation.

---

## Mock Provider

Pravaah currently includes a Mock AI Provider.

Purpose:

* Development
* Testing
* Framework Verification

Example startup log:

```text
Mock AI provider initialised
(no API calls will be made)
```

This allows developers to build and test AI workflows without incurring API costs.

---

## CRM Plugin Example

The CRM plugin demonstrates AI integration in a real application.

---

### Lead Scoring

When a customer is created:

```text
Customer Created
        ↓
after_create Event
        ↓
AI Lead Scoring
        ↓
Score Assigned
```

This allows the system to evaluate leads automatically.

---

### Email Drafting

Custom endpoint:

```text
POST /crm/custom/customers/{id}/draft_email
```

Workflow:

```text
Customer Selected
        ↓
Customer Context Retrieved
        ↓
AI Prompt Generated
        ↓
Email Draft Created
        ↓
Response Returned
```

This reduces manual effort for sales teams.

---

## Example Usage

A plugin can access the AI service through the registry.

```python
ai = registry.get_service("ai")

response = await ai.generate(
    prompt="Draft an introductory sales email"
)
```

The plugin remains independent of the underlying provider.

---

## Workflow Integration

The AI Layer works naturally with the Event System.

Example:

```text
Customer Created
        ↓
Event Triggered
        ↓
Hook Executed
        ↓
AI Analysis
        ↓
Customer Updated
```

This enables intelligent automation without additional complexity.

---

## Future AI Capabilities

Pravaah's architecture supports a wide range of future AI features.

### Content Generation

Generate:

* Emails
* Reports
* Summaries
* Marketing Content

---

### Classification

Automatically categorize:

* Leads
* Support Tickets
* Customer Requests

---

### Summarization

Generate concise summaries from large amounts of data.

---

### Recommendation Engines

Provide intelligent recommendations based on business context.

---

### Workflow Decision Making

Use AI to determine workflow paths dynamically.

Example:

```text
Lead Created
      ↓
AI Evaluation
      ↓
High Priority?
      ↓
Yes → Assign Sales Team
No  → Nurture Workflow
```

---

## AI and Workflow Orchestration

The AI Layer becomes increasingly powerful when combined with workflows.

Future vision:

```text
Event
   ↓
Workflow Engine
   ↓
AI Decision
   ↓
Next Action
   ↓
Workflow Continues
```

This creates intelligent, self-adapting business processes.

---

## Security Considerations

When integrating AI providers, developers should consider:

* Data Privacy
* API Key Management
* Prompt Validation
* Rate Limiting
* Audit Logging

The AI Layer is designed to centralize these concerns.

---

## Benefits

### Flexibility

Switch providers without changing application code.

---

### Scalability

Use AI across multiple plugins and workflows.

---

### Maintainability

Keep AI logic separate from business logic.

---

### Testability

Use mock providers during development.

---

### Future Readiness

Support emerging AI capabilities without redesigning applications.

---

## Road Ahead

Planned AI enhancements include:

* Multi-Provider Support
* Prompt Templates
* AI Workflow Actions
* Embedding Support
* Retrieval-Augmented Generation (RAG)
* Local Model Integration
* AI Monitoring

These features will further strengthen Pravaah's AI-native architecture.

---

## Summary

The AI Layer transforms Pravaah from a traditional backend framework into an intelligent application platform.

By providing a unified interface for AI capabilities, Pravaah enables developers to build powerful, workflow-driven applications that combine automation, events, and intelligence.

The AI Layer is a key part of the framework's vision:

**Everything Flows. Intelligence Included.**
