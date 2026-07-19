# Weatherapp

Weatherapp is a self-hosted weather dashboard for a Raspberry Pi k3s homelab. It provides:

- Current conditions
- Hourly and daily forecasts
- NWS alert visibility
- Golf and lawn recommendation cards
- Prometheus telemetry from the API

## Stack

- Backend: FastAPI (`backend/`)
- Frontend: React + Vite (`frontend/`)
- Delivery: Docker + Helm chart (`deploy/chart/weatherapp`)
- CI: GitHub Actions tests, multi-arch image publishing, and OCI Helm chart release publishing

## Repository layout

```text
backend/                 FastAPI application, weather integration, tests
frontend/                React dashboard
deploy/chart/weatherapp  Helm chart for API + web deployment
observability/           Grafana dashboard JSON
docs/                    Architecture, API, and operations documentation
```

## Local development

### Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Node.js 18+
- Copy `.env.example` to `.env` and set your `NWS_USER_AGENT` contact string

### Start the stack

```bash
# 1. Start backend (builds image, starts container on :8000)
make local-up

# 2. Start frontend dev server (separate terminal, runs on :5173)
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. The frontend proxies `/api`, `/health`, and `/metrics` to the backend container.

### Stop the stack

```bash
make local-down          # stop and remove backend container
# Ctrl+C the frontend dev server terminal
```

### Other useful commands

```bash
make local-logs          # tail backend container logs
make local-status        # show container status (docker compose ps)
```

### Agentic shortcut (GitHub Copilot)

A skill is defined at `.github/skills/weatherapp-local-preflight/SKILL.md` — readable, plain-English steps covering the full startup, health checks, and browser preview workflow.

The Copilot CLI extension in `.github/extensions/weatherapp-local-tester/` automates execution. From a project session, type `/weather-local-test` in the chat composer. The preflight agent builds the backend, starts the frontend, health-checks both, and opens the browser preview automatically. Type `/weather-local-stop` to tear down.

### Backend-only (no Docker)

```bash
cd backend
pip install -e ".[dev]"
uvicorn weather_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

Run all tests:

```bash
make backend-test        # pytest
make frontend-test       # vitest (CI mode, no watch)
```

Or individually:

```bash
# Backend
cd backend && pytest tests

# Frontend
cd frontend && npm run test:ci
```

## Helm deployment (local chart)

```bash
helm upgrade --install weatherapp ./deploy/chart/weatherapp \
  --namespace weather \
  --create-namespace \
  --set api.image.tag=<sha-tag> \
  --set web.image.tag=<sha-tag>
```

## k3s-infrastructure integration

Production handoff uses an OCI-published chart and Flux chart version pinning in `k3s-infrastructure`.

- OCI chart target: `oci://ghcr.io/dylanwhitetech/charts`
- Chart name: `weatherapp`
- Infra promotion model: bump `spec.chart.spec.version` in `kubernetes/apps/weatherapp/helmrelease.yaml`

See `docs/operations.md` for release and handoff details.
