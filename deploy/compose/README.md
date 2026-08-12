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
| `ml` | TEI embed (`BAAI/bge-m3` :8080) + rerank (`BAAI/bge-reranker-v2-m3` :8081); large first download |
| `auth` | Zitadel + dedicated Postgres 16 (`zitadel-db`) |
| `obs` | Langfuse + Tempo (OTLP :4318) |

Default TEI image is digest-pinned **linux/amd64** `cpu-1.9`
(`sha256:c26a226262ad4ff3330fb30b76653c1bb65da2fcf413b92284545a010e0a8a48`).
On Apple Silicon / aarch64, override with this **arm64** digest (verified `Architecture: arm64`;
upstream versioned `cpu-arm64-1.9` tags are not consistently published):

```bash
export SIFT_TEI_IMAGE=ghcr.io/huggingface/text-embeddings-inference@sha256:35c50d7494de22deecdb783b8f5b7e1d05765709bd90071b03469b9440d28656
docker compose -f deploy/compose/dev.yml --profile ml up -d
```

Auth bootstrap (after `--profile auth` is healthy):

```bash
uv run python tools/auth/bootstrap_zitadel.py   # writes deploy/compose/zitadel-dev.env
set -a && source deploy/compose/zitadel-dev.env && set +a
# Device login: sift login   (admin: sift-admin@sift.localhost / SiftAdmin1!)
```

Uploads: `tusd` on host `:1080` (`/files/`). Resume E2E: `tools/e2e/test_tus_resume.py`.

TEI smoke (after `--profile ml` is healthy):

```bash
curl -s http://localhost:8080/health
uv run pytest -q -m integration tests/integration/test_tei_smoke.py
```
