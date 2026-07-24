---
name: weatherapp-local-preflight
description: "Run the full local weatherapp stack, verify backend and frontend health, and open the browser preview. Use this when the user wants a local smoke test, dev-stack startup, or pre-push verification."
license: MIT
compatibility: "Cross-platform. Requires Docker Desktop, Node.js 18+, and a repo-root .env with NWS_USER_AGENT configured."
argument-hint: "Optional: ask to rebuild the backend, reinstall frontend dependencies, or skip opening the browser preview."
allowed-tools: shell
---

## Weatherapp Local Preflight

Starts the weatherapp local development stack from the current worktree and
confirms that both services are healthy before reporting success.

- **Backend:** FastAPI app running in Docker Compose on `:8000`
- **Frontend:** Vite dev server on `:5173` (proxies `/api`, `/health`, `/metrics` to `:8000`)

## Output Contract (Required)

Before finishing, all of the following must be true:

1. The backend is reachable on `http://localhost:8000/health/live`.
2. The frontend is reachable on `http://localhost:5173`.
3. The final response states which services are up and gives the local URLs.
4. If startup fails, report which phase failed and the most useful next action.

## Workflow

Copy and follow this checklist:

```text
- [ ] Phase 1: Stop conflicting local processes and confirm prerequisites
- [ ] Phase 2: Start the backend with Docker Compose
- [ ] Phase 3: Install frontend dependencies if needed and start Vite
- [ ] Phase 4: Validate backend and frontend health
- [ ] Phase 5: Open browser preview when requested and report status
```

## Prerequisites

- Docker Desktop must be running
- Node.js 18+ must be installed
- `.env` file must exist at repo root (copy from `.env.example` and set `NWS_USER_AGENT`)

## Phase 1: Clean start

1. Stop any existing local stack to avoid port conflicts:

   ```bash
   make local-down
   ```

2. Also stop any existing frontend dev server on `:5173`.

## Phase 2: Start backend

1. Start the backend using Docker Compose:

   ```bash
   make local-up
   ```

   This builds the local backend image and starts the container on `:8000`.

## Phase 3: Start frontend

1. Install frontend dependencies if `frontend/node_modules` does not exist:

   ```bash
   cd frontend && npm ci
   ```

2. Start the frontend dev server in the background:

   ```bash
   cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
   ```

## Phase 4: Validate health

1. Wait for both services to become healthy:

   - Backend: poll `GET http://localhost:8000/health/live` until HTTP 200
   - Frontend: poll `GET http://localhost:5173` until HTTP 200
   - Timeout after 90 seconds; if either fails, report which service is down

## Phase 5: Report and preview

1. Open the browser preview at `http://localhost:5173` when requested.
2. Report the backend and frontend URLs.
3. Tell the user how to stop the stack when finished.

## Shutdown

```bash
make local-down          # stops and removes the backend container
# Ctrl+C the frontend dev server terminal, or:
# On Windows: taskkill /PID <frontend-pid> /T /F
```

## Gotchas

- **Backend fails to start:** run `make local-logs` to tail Docker Compose logs
- **Frontend fails to start:** check for port conflicts on `:5173` or run `npm ci` manually
- **NWS API errors in backend logs:** verify `NWS_USER_AGENT` is set in `.env`
- **Image build fails:** ensure Docker Desktop is running; try `docker compose build --no-cache`
