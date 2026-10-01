# Weatherapp

Weatherapp is a self-hosted weather dashboard served at <https://weatherapp.dylanlabs.dev> from a Raspberry Pi k3s cluster. It provides:

- Current conditions
- Hourly and daily forecasts
- NWS alert visibility
- Weather map layers for precipitation, fires, air quality, temperature, and wind
- Golf and lawn recommendation cards
- Prometheus telemetry from the API

## Stack

- Backend: FastAPI (`backend/`)
- Frontend: React + Vite (`frontend/`)
- Delivery: Docker + Helm chart (`deploy/chart/weatherapp`)
- CI: GitHub Actions tests, chart smoke testing, SHA-tagged image publishing, and release-please-driven OCI Helm chart releases

## Repository layout

```text
backend/                 FastAPI application, weather integration, map overlays, tests
frontend/                React dashboard and Vitest tests
deploy/chart/weatherapp  Helm chart for API + web deployment
observability/           Grafana dashboard JSON
docs/                    Architecture, API, operations, and runbook docs
```

## Local development

### Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Node.js 20.19+, 22.12+, or 24+
- Copy `.env.example` to `.env` and set your `NWS_USER_AGENT` contact string

### Start the stack

```bash
# 1. Start backend (builds image, starts container on :8000)
make local-up

# 2. Start frontend dev server (separate terminal, runs on :5173)
cd frontend && npm ci && npm run dev
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

Run the same local quality gates enforced by CI:

```bash
# Backend lint
cd backend && python -m ruff check src tests

# Frontend lint and build
cd frontend && npm run lint
cd frontend && npm run build

# Helm chart lint
helm lint deploy/chart/weatherapp
```

CI also runs a `chart-smoke` job that builds both images, installs the chart into a throwaway kind cluster, waits for readiness, and curls `/health/live`, `/health/ready`, `/api/v1/weather`, and the web root.

## Helm deployment (local chart)

```bash
helm upgrade --install weatherapp ./deploy/chart/weatherapp \
  --namespace weather \
  --create-namespace \
  --set api.image.tag=<sha-tag> \
  --set web.image.tag=<sha-tag>
```

## Production, release, and infrastructure handoff

Production uses the OCI chart at `oci://ghcr.io/dylanwhitetech/charts` with chart name `weatherapp`. Release automation is owned by release-please: merge releasable Conventional Commit PRs to `main`, merge the generated release PR, then merge the generated infra promotion PR in `dylanwhitetech/k3s-infrastructure` so Flux deploys the new chart version.

See [docs/operations.md](docs/operations.md) for the shipping flow and [docs/architecture.md](docs/architecture.md) for the runtime topology.
