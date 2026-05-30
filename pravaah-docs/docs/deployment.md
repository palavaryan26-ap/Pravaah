# Deployment

Pravaah is designed to be deployable across multiple environments, from local development machines to cloud infrastructure.

This guide covers the currently supported deployment methods.

---

# Deployment Overview

Pravaah can be deployed using:

* Local Development Environment
* Docker Containers
* Render
* Virtual Machines
* Future Kubernetes Deployments

The framework follows a cloud-friendly architecture and can be containerized easily.

---

# Local Development

Local deployment is recommended during development and testing.

## Prerequisites

* Python 3.11+
* Git
* Pip
* Virtual Environment Support

---

## Clone Repository

```bash
git clone https://github.com/palavaryan26-ap/Pravaah.git
cd Pravaah
```

---

## Create Virtual Environment

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

---

## Start Framework

```bash
pravaah run
```

Alternative:

```bash
uvicorn pravaah.app.main:create_app --factory --reload
```

Expected Output:

```text
[Pravaah] Flowing on 0.0.0.0:8000
```

---

## Verify Deployment

Framework Root:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

# Docker Deployment

Pravaah includes Docker support for reproducible deployments.

---

## Build Docker Image

From the project root:

```bash
docker build -t pravaah .
```

---

## Verify Image

```bash
docker images
```

Expected Output:

```text
REPOSITORY   TAG
pravaah      latest
```

---

## Run Container

```bash
docker run -p 8000:8000 pravaah
```

Application becomes available at:

```text
http://localhost:8000
```

---

## Run Detached

```bash
docker run -d -p 8000:8000 pravaah
```

---

## View Logs

```bash
docker logs <container-id>
```

---

## Stop Container

```bash
docker stop <container-id>
```

---

# Docker Architecture

```text
Client
   ↓
Docker Container
   ↓
Pravaah Framework
   ↓
SQLite Database
```

This deployment method is ideal for development and lightweight production workloads.

---

# Render Deployment

Render provides a simple cloud deployment experience for Pravaah.

---

## Step 1: Push to GitHub

Ensure your code is committed.

```bash
git add .
git commit -m "Deploy Pravaah"
git push origin main
```

---

## Step 2: Create Render Account

Sign in to Render using GitHub.

---

## Step 3: Create New Web Service

Select:

```text
New +
   ↓
Web Service
```

Choose the Pravaah repository.

---

## Step 4: Configure Service

### Environment

```text
Python
```

### Build Command

```bash
pip install -e .[ai]
```

### Start Command

```bash
pravaah run --host 0.0.0.0 --port $PORT
```

---

## Step 5: Deploy

Render automatically:

* Builds the application
* Installs dependencies
* Starts the framework
* Exposes a public URL

Example:

```text
https://pravaah.onrender.com
```

---

# Render Deployment Architecture

```text
Internet
    ↓
Render Load Balancer
    ↓
Pravaah Instance
    ↓
Database
```

This provides a simple production-ready deployment option.

---

# Environment Variables

Future deployments may require:

```text
DATABASE_URL
AI_PROVIDER
OPENAI_API_KEY
SECRET_KEY
DEBUG
```

Example:

```bash
export OPENAI_API_KEY=your_key_here
```

Environment variables should never be hardcoded.

---

# Production Considerations

For production deployments, consider:

### Database

Replace SQLite with:

* PostgreSQL
* MySQL

---

### Monitoring

Integrate:

* Logging
* Metrics
* Error Tracking

---

### Security

Enable:

* HTTPS
* API Authentication
* Secret Management
* Rate Limiting

---

### Scaling

Future versions of Pravaah will support:

* Horizontal Scaling
* Distributed Workflows
* Workflow Persistence

---

# Deployment Verification Checklist

Before sharing a deployment:

```text
✓ Application Starts

✓ Routes Accessible

✓ Swagger UI Available

✓ ReDoc Available

✓ CRUD APIs Functional

✓ Plugins Loaded

✓ AI Service Registered

✓ Database Connected
```

---

# Example Production Deployment

```text
GitHub
   ↓
Render
   ↓
Pravaah
   ↓
PostgreSQL
```

This architecture is suitable for early-stage production applications.

---

# Future Deployment Targets

Planned deployment support includes:

* Kubernetes
* AWS ECS
* Azure Container Apps
* Google Cloud Run
* Temporal Worker Deployment
* Multi-Service Architectures

These deployment options align with the long-term vision of Pravaah as a workflow-oriented platform.

---

# Summary

Pravaah can be deployed locally, inside Docker containers, or directly to cloud platforms such as Render.

The framework's container-friendly architecture makes deployment straightforward while providing a foundation for future scalability and workflow orchestration capabilities.

By combining automated deployment, plugin-based architecture, and AI-native services, Pravaah enables developers to move quickly from development to production.

**Everything Flows. Everywhere.**
