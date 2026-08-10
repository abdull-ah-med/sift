.PHONY: setup up seed web api worker mcp-proxy test integration eval lint typecheck

setup:
	./tools/dev/setup.sh

up:
	docker compose -f deploy/compose/dev.yml up -d

seed:
	@echo "seed lands in Phase 1"

web:
	pnpm --filter @sift/web dev

api:
	@echo "api reload lands with the FastAPI stub PR"

worker:
	@echo "worker lands with the Taskiq stub PR"

mcp-proxy:
	pnpm --filter @sift/mcp-proxy dev

test:
	uv run pytest -q
	pnpm -r test

lint:
	uv run ruff check .
	uv run ruff format --check .
	pnpm -r lint

typecheck:
	uv run mypy libs/sift-core/src
	pnpm -r typecheck

integration:
	uv run pytest tests/integration -m "not slow"

eval:
	@echo "eval harness lands in Phase 3"
