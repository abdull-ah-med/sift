# Compose smoke helpers (Phase 0)

.PHONY: compose-config compose-up compose-down compose-ps

compose-config:
	docker compose -f deploy/compose/dev.yml config >/dev/null

compose-up:
	docker compose -f deploy/compose/dev.yml up -d --build

compose-down:
	docker compose -f deploy/compose/dev.yml down -v

compose-ps:
	docker compose -f deploy/compose/dev.yml ps
