# compose

Docker Compose profiles for local development.

## Quick start

```bash
docker compose -f deploy/compose/dev.yml up -d --build
curl -s http://localhost:8000/health
```

Core services (default profile): Postgres/ParadeDB, Valkey, SeaweedFS, sift-api, sift-worker, sift-web.

Optional profiles:

| Profile | Services |
|---|---|
| `ml` | TEI embed + rerank (large model download) |
| `auth` | Zitadel |
| `obs` | Langfuse + Tempo (OTLP :4318) |

```bash
docker compose -f deploy/compose/dev.yml --profile ml up -d
```

Production single-node stack: `deploy/compose/prod-single.yml` (Caddy + resource limits).
