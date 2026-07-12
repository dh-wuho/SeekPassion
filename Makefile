.PHONY: dev dev-api dev-web migrate seed test lint

dev-api:
	uv run --package seekpassion-api uvicorn seekpassion_api.main:app --app-dir apps/api/src --reload --port 8000

dev-web:
	cd apps/web && pnpm dev --port 3000

dev:
	$(MAKE) dev-api & \
	trap 'kill %1' EXIT; \
	$(MAKE) dev-web

migrate:
	cd apps/api && uv run --package seekpassion-api alembic upgrade head

seed:
	uv run --package seekpassion-api python -m seekpassion_api.seed

test:
	uv run --package seekpassion-api pytest apps/api/tests
	cd apps/web && pnpm lint && pnpm exec tsc --noEmit && pnpm build

lint:
	uv run ruff check apps/api
	cd apps/web && pnpm lint
