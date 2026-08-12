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
| `ml` | TEI embed (`BAAI/bge-m3` :8080) + rerank (`BAAI/bge-reranker-v2-m3` :8081); healthchecks on `/health` (large first download) |
| `auth` | Zitadel + dedicated Postgres 16 (`zitadel-db`) |
| `obs` | Langfuse + Tempo (OTLP :4318) |

Auth bootstrap (after `--profile auth` is healthy):

```bash
uv run python tools/auth/bootstrap_zitadel.py   # writes deploy/compose/zitadel-dev.env
set -a && source deploy/compose/zitadel-dev.env && set +a
# Device login: sift login   (admin: sift-admin@sift.localhost / SiftAdmin1!)
```

Uploads: `tusd` on host `:1080` (`/files/`). Resume E2E: `tools/e2e/test_tus_resume.py`.
