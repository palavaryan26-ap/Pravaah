# Pravaah

> *Everything flows.*

Pravaah is a modern, AI-native, plugin-driven backend framework designed for scalable enterprise application development through flow-oriented architecture.

It combines the speed of FastAPI, the architectural rigor of enterprise systems, and the intelligence of AI-native platforms into a single, modular developer ecosystem.

---

## 🌊 Core Philosophy: "Everything Flows"

Pravaah is not just a backend framework; it is an **orchestration engine**.
Traditional backends are static: data goes in, data comes out. Pravaah treats your business operations as dynamic workflows. 

- **Modular Plugin System**: Every feature is an isolated, swappable plugin.
- **Dynamic CRUD Engine**: Generate highly-optimized, paginated REST APIs in three lines of code.
- **Event-Driven Workflows**: Decouple logic with asynchronous event hooks (`@after_create`, `@on_event`).
- **Native AI Layer**: Built-in LLM orchestration seamlessly integrates intelligence into your business flows.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- SQLite (default) or PostgreSQL

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/pravaah.git
cd pravaah

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

# Install the framework
pip install -e .[ai]
```

### Running the Server

Pravaah comes with a powerful developer CLI built on Typer.

```bash
# Start the development server
pravaah run --reload

# Show framework info and registry status
pravaah info

# List all loaded plugins, models, hooks, and routes
pravaah list-plugins
pravaah list-models
pravaah list-hooks
pravaah routes
```

### Running with Docker

Pravaah is enterprise-ready and containerized out of the box.

```bash
docker-compose up -d --build
```

The app will be available at `http://localhost:8000`.

## 🧩 The Plugin Ecosystem

Everything in Pravaah is a plugin. You can scaffold a new plugin instantly using the CLI:

```bash
pravaah init-plugin my_feature
```

This generates a cleanly structured plugin directory:
```
pravaah/plugins/my_feature/
├── __init__.py      # Plugin setup and routing
└── hooks.py         # Event automation
```

## 🏗️ Demo: Pravaah CRM

Pravaah comes with a built-in CRM plugin (`pravaah/plugins/crm`) that showcases the full power of the framework. **Pravaah CRM is an AI-native customer operations platform.**

When you run the framework, the CRM automatically demonstrates:
1. **Dynamic APIs**: Fully auto-generated endpoints for `Customer`, `Deal`, and `Activity` models.
2. **AI Lead Scoring**: An `@after_create` hook that silently evaluates new customers using the native AI Service and assigns a lead score.
3. **Workflow Automation**: An `@after_update` hook that automatically logs an `Activity` the moment a `Deal` is marked as 'won'.
4. **Intelligent Endpoints**: A custom `POST /crm/custom/customers/{id}/draft_email` route that uses AI to draft highly contextual client emails based on real-time CRM data.

## ⚙️ Configuration

Configuration is managed via `config/pravaah.yaml` or Environment Variables.

```yaml
app:
  name: "Pravaah"
  debug: true
database:
  provider: "sqlite"
ai:
  enabled: true
  provider: "mock" # Change to 'openai' for production
plugins:
  auto_discover: true
  plugin_dirs:
    - "pravaah/plugins"
```

## 📖 License

This project is licensed under the MIT License.
