# Copilot Instructions — weatherapp

## What this repo is

Weatherapp is a self-hosted weather dashboard for a k3s homelab. It pulls live
conditions and forecasts from the NWS API (no API key required). Backend is
FastAPI; frontend is React + Vite. It deploys via Helm to k3s managed by Flux.

## Repo layout

```
backend/                 FastAPI app, NWS client, cache, recommendations, tests
frontend/                React + Vite dashboard, vitest tests
deploy/chart/weatherapp  Helm chart (OCI-published to ghcr.io/dylanwhitetech/charts)
.github/extensions/      Copilot CLI extensions (local preflight agent)
.github/workflows/       CI: test, image publish, chart release
docker-compose.yml       Local dev backend stack
Makefile                 Convenience targets: local-up/down/logs/status, test
observability/           Grafana dashboard JSON
docs/                    Architecture, API, and operations docs
```

## Local development workflow

Backend runs in Docker Compose. Frontend runs on the host.

```bash
# Copy .env.example → .env and set NWS_USER_AGENT
make local-up            # docker compose up -d --build (backend on :8000)
cd frontend && npm run dev  # dev server on :5173 (proxies /api → :8000)
make local-down          # stop backend
```

**Agentic shortcut:** see `.github/skills/weatherapp-local-preflight/SKILL.md`
for the full skill. The Copilot CLI extension in `.github/extensions/weatherapp-local-tester/`
automates execution — trigger with `weatherapp_local_test` tool or `/weather-local-test`.

## Testing

```bash
make backend-test        # pytest backend/tests
make frontend-test       # vitest --run frontend
```

## Code conventions

- Backend: Python 3.12, FastAPI, ruff for linting, pytest for tests
- Frontend: TypeScript, React 18, Vite, vitest + jsdom for tests
- All async backend code uses `asyncio`; NWS calls go through `services/weather.py`
- Never call NWS API directly from route handlers — use the service layer
- Unit conversion helpers: `_mps_to_mph` (wind), `_c_to_f` (temp) in `weather.py`

## CI / release model

- `test.yml` — runs on every PR: pytest + vitest + helm lint
- `images.yml` — pushes multi-arch images to GHCR on merge to `main`
- `release-chart.yml` — triggered by semver tag `vX.Y.Z`; publishes OCI Helm
  chart to `oci://ghcr.io/dylanwhitetech/charts`

## Deployment

Production runs in k3s via Flux. The HelmRelease in `k3s-infrastructure`
pins `spec.chart.spec.version` to a specific chart release. Infra promotion =
bump that version after a chart release.

Flux auth secret for private GHCR chart: `ghcr-weatherapp-charts-auth`
(created once by operator; see `docs/operations.md`).

## NWS API notes

- Requires `NWS_USER_AGENT` header with a contact string (policy requirement)
- Wind speed from observations comes in m/s — use `_mps_to_mph`
- Wind direction from observations is degrees — convert with `_wind_direction`
- Forecast wind speed is a string like "10 to 15 mph" — parse with `_parse_wind_values`
