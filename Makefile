.PHONY: backend-test frontend-test frontend-build \
        local-up local-down local-logs local-status

backend-test:
	python -m pytest backend/tests

frontend-test:
	cd frontend && npm run test:ci

frontend-build:
	cd frontend && npm run build

# Local dev stack ---------------------------------------------------------------
# Backend runs in Docker Compose; open a second terminal for the frontend:
#   cd frontend && npm run dev
#
# Copy .env.example to .env and set NWS_USER_AGENT before first run.

local-up:
	docker compose up -d --build

local-down:
	docker compose down

local-logs:
	docker compose logs -f api

local-status:
	docker compose ps
