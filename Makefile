.PHONY: backend-test frontend-test frontend-build

backend-test:
	python -m pytest backend/tests

frontend-test:
	cd frontend && npm run test:ci

frontend-build:
	cd frontend && npm run build
