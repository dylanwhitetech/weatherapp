---
name: weatherapp-worktree-hydrate
description: "Hydrate a weatherapp worktree with local environment config, verify provider key readiness, run targeted checks, and relaunch preview. Use this at the start of new worktree sessions when local API keys or .env drift are likely."
license: MIT
compatibility: "Cross-platform. Requires an existing local weatherapp checkout with a usable .env or fallback to .env.example."
argument-hint: "Optional: include source checkout path for .env hydration, whether to run full tests, and whether to relaunch browser preview."
allowed-tools: shell
---

## Weatherapp Worktree Hydrate

Hydrates a fresh worktree so map layers and local validation work immediately.

## Output Contract (Required)

Before finishing, all of the following must be true:

1. Worktree `.env` exists and key presence status is reported without exposing secret values.
2. Backend and frontend checks requested by the user are complete.
3. Service health for backend and frontend is reported if servers are started.
4. Final output clearly lists any missing keys still required for full map functionality.

## Workflow

```text
- [ ] Phase 1: Hydrate .env into the active worktree
- [ ] Phase 2: Validate key presence (without printing key values)
- [ ] Phase 3: Run requested validation commands
- [ ] Phase 4: Restart local services and verify health
- [ ] Phase 5: Refresh side-panel browser preview and report readiness
```

## Phase 1: Hydrate `.env`

1. If `./.env` is missing, copy it from the main local checkout (same repository).
2. If no source `.env` exists, copy from `./.env.example` and mark missing keys explicitly.

## Phase 2: Validate key presence

Check only presence/state (`set`, `empty`, `not-set`, `missing`) for:

- `NWS_USER_AGENT`
- `AIRNOW_API_KEY`

Never print actual key values.

## Phase 3: Validation commands

Run the smallest relevant checks first:

```bash
cd backend && python -m ruff check src tests
cd backend && python -m pytest -q
cd frontend && npm run test:ci
cd frontend && npm run build
```

## Phase 4: Start/restart local services

Preferred route:

```bash
make local-down
make local-up
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
```

Fallback when Docker is unavailable:

```bash
cd backend && python -m uvicorn weather_api.main:app --app-dir src --host 0.0.0.0 --port 8000
cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
```

## Phase 5: Health and preview

Confirm:

- `http://localhost:8000/health/live` is 200
- `http://localhost:5173` is 200

Then refresh/open the side-panel browser preview.

## Gotchas

- A user may update `.env` in the main checkout but not in the worktree.
- Without `AIRNOW_API_KEY`, air-quality layer remains selectable but shows an unavailable message.
- Keep map provider keys server-side only; never expose them in frontend code or logs.
