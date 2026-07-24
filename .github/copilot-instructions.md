# Copilot Instructions — weatherapp

## Read these first

- `AGENTS.md`
- `CONTRIBUTING.md`

Before creating a new agent or skill, check `github/awesome-copilot` first:

- `https://awesome-copilot.github.com/agents`
- `https://awesome-copilot.github.com/skills`
- `https://awesome-copilot.github.com/llms.txt`

Reuse an existing pattern when it fits. Do not invent a new structure when a
close upstream example already exists.

## What this repo is

Weatherapp is a self-hosted weather dashboard for a k3s homelab. It pulls live
conditions and forecasts from the NWS API. Backend is FastAPI; frontend is
React + Vite. It deploys via Helm to k3s managed by Flux.

## Repo layout

```text
backend/                 FastAPI app, NWS client, cache, recommendations, tests
frontend/                React + Vite dashboard, vitest tests
deploy/chart/weatherapp  Helm chart (OCI-published to ghcr.io/dylanwhitetech/charts)
agents/                  Custom repo agents
.github/skills/          Repo runtime Copilot skills
.github/extensions/      Copilot CLI extensions
.github/workflows/       CI: tests, image publish, chart release
docker-compose.yml       Local dev backend stack
Makefile                 Local test and lifecycle commands
observability/           Grafana dashboard JSON
docs/                    Architecture, API, and operations docs
```

## Code standards source of truth

All code standards are centralized in `AGENTS.md` for human readability:

- `Shared standards (portable baseline)`
- `Weatherapp engineering rules`

When standards change, update `AGENTS.md` first and keep this file as a concise
execution and routing guide.

## AI customization rules

- Repo runtime skills live in `.github/skills/`.
- Custom agents live in `agents/`.
- New skills and agents should follow `awesome-copilot` naming, frontmatter,
  and checklist patterns.
- If you add or update a skill or agent, mention the upstream example used as a
  starting point in the PR description.

## Local development workflow

Backend runs in Docker Compose. Frontend runs on the host.

```bash
# Copy .env.example -> .env and set NWS_USER_AGENT
make local-up
cd frontend && npm run dev
make local-down
```

Agentic shortcut:

- skill: `.github/skills/weatherapp-local-preflight/SKILL.md`
- extension/tooling: `.github/extensions/weatherapp-local-tester/`

## Validation commands

```bash
make backend-test
make frontend-test
cd frontend && npm run build
cd frontend && npm run lint
```

If backend tooling is installed, also run:

```bash
cd backend && python -m ruff check src tests
```

## CI / release model

- `test.yml` currently runs backend tests, frontend tests, and frontend build
- `images.yml` pushes multi-arch images to GHCR on merge to `main`
- `release-chart.yml` publishes the OCI Helm chart on semver tags

## Deployment

Production runs in k3s via Flux. Infra promotion is a chart version bump in the
separate `k3s-infrastructure` repo after the chart release is published.

See `docs/operations.md` for operational details.
