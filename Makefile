.PHONY: setup up seed web api worker mcp-proxy test integration eval lint typecheck migrate migrate-down

setup:
	./tools/dev/setup.sh

up:
	docker compose -f deploy/compose/dev.yml up -d --build

seed:
	@echo "seed lands in Phase 1"

migrate:
	uv run alembic -c tools/db/alembic.ini upgrade head

migrate-down:
	uv run alembic -c tools/db/alembic.ini downgrade -1

web:
	pnpm --filter @sift/web dev

api:
	uv run uvicorn sift_api.main:app --reload --app-dir services/api/src

worker:
	uv run python -m sift_worker

mcp-proxy:
	pnpm --filter @sift/mcp-proxy dev

test:
	uv run pytest -q
	pnpm -r test

lint:
	uv run ruff check libs services apps tests tools
	uv run ruff format --check libs services apps tests tools
	pnpm -r lint

typecheck:
	uv run mypy libs/sift-core/src libs/sift-parse/src libs/sift-ingest/src services/api/src
	pnpm -r typecheck

integration:
	uv run pytest tests/integration -m "not slow"

eval:
	@echo "eval harness lands in Phase 3"
