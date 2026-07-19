---
name: weatherapp-local-preflight
description: >
  Runs the full local weatherapp dev stack (backend + frontend), validates
  health endpoints, and opens the browser preview. Use this when asked to
  start the app locally, run a local smoke test, or verify the stack is
  working before pushing changes.
allowed-tools: shell
---

## Overview

This skill starts the weatherapp local development stack from the current
worktree and confirms both services are healthy.

- **Backend:** FastAPI app running in Docker Compose on `:8000`
- **Frontend:** Vite dev server on `:5173` (proxies `/api`, `/health`, `/metrics` to `:8000`)

## Prerequisites

- Docker Desktop must be running
- Node.js 18+ must be installed
- `.env` file must exist at repo root (copy from `.env.example` and set `NWS_USER_AGENT`)

## Steps

1. **Stop any existing local stack** to avoid port conflicts:

   ```bash
   make local-down
   # Also kill any existing frontend dev server on :5173
   ```

2. **Start the backend** using Docker Compose:

   ```bash
   make local-up
   ```

   This runs `docker compose up -d --build`, which builds the `weatherapp-api-local`
   image from `backend/Dockerfile` and starts the container on `:8000`.

3. **Install frontend dependencies** if `frontend/node_modules` does not exist:

   ```bash
   cd frontend && npm ci
   ```

4. **Start the frontend dev server** in the background:

   ```bash
   cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
   ```

5. **Wait for both services to become healthy:**

   - Backend: poll `GET http://localhost:8000/health/live` until HTTP 200
   - Frontend: poll `GET http://localhost:5173` until HTTP 200
   - Timeout after 90 seconds; if either fails, report which service is down

6. **Open the browser preview** at `http://localhost:5173` so the user can
   visually verify the app.

7. **Report status** — confirm backend and frontend are up, provide the URLs,
   and tell the user to run `make local-down` (plus stop the frontend terminal)
   when finished.

## Stopping the stack

```bash
make local-down          # stops and removes the backend container
# Ctrl+C the frontend dev server terminal, or:
# On Windows: taskkill /PID <frontend-pid> /T /F
```

## Troubleshooting

- **Backend fails to start:** run `make local-logs` to tail Docker Compose logs
- **Frontend fails to start:** check for port conflicts on `:5173` or run `npm ci` manually
- **NWS API errors in backend logs:** verify `NWS_USER_AGENT` is set in `.env`
- **Image build fails:** ensure Docker Desktop is running; try `docker compose build --no-cache`
