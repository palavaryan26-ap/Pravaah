# Getting Started

This guide will help you install, configure, and run Pravaah locally.

## Prerequisites

Before installing Pravaah, ensure you have the following:

* Python 3.11 or later
* Git
* pip
* Virtual Environment support

Verify your Python version:

```bash
python --version
```

Expected output:

```text
Python 3.11+
```

---

## Clone the Repository

```bash
git clone https://github.com/palavaryan26-ap/Pravaah.git
cd Pravaah
```

---

## Create a Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

Development dependencies:

```bash
pip install -r requirements-dev.txt
```

---

## Run the Framework

Start Pravaah using:

```bash
pravaah run
```

or

```bash
uvicorn pravaah.app.main:create_app --factory --reload
```

Expected output:

```text
[Pravaah] Flowing on 0.0.0.0:8000
```

---

## Verify Installation

Open:

### Framework Root

```text
http://localhost:8000
```

### Swagger Documentation

```text
http://localhost:8000/docs
```

### ReDoc Documentation

```text
http://localhost:8000/redoc
```

---

## Project Structure

```text
Pravaah/
│
├── pravaah/
│   ├── app/
│   ├── engine/
│   ├── plugins/
│   ├── registry/
│   └── services/
│
├── config/
├── tests/
├── Dockerfile
├── docker-compose.yaml
└── README.md
```

---

## Available Demo Plugins

The framework currently includes:

### Hello Plugin

A simple verification plugin used to validate plugin loading.

### Notes Plugin

Demonstrates dynamic CRUD generation.

### CRM Plugin

Demonstrates:

* Customer management
* Deal management
* Activity tracking
* AI lead scoring
* Workflow automation
* AI email drafting

---

## Next Steps

Continue with:

* Architecture
* Plugin System
* CRUD Engine
* Event System
* AI Layer
* CRM Demo

to understand how Pravaah works internally.

**Everything Flows.**
