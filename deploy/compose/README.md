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

## Local demo

Record a laptop demo after Compose and TEI are up. Ollama runs on the host, not in Compose.

1. Start core services (`make up` or `docker compose -f deploy/compose/dev.yml up -d`), then the `ml` profile for TEI. On Apple Silicon, set `SIFT_TEI_IMAGE` to the arm64 digest in the TEI section above. Do not unpin to `latest`.
2. Install [Ollama](https://ollama.com), then `ollama pull llama3.1`.
3. Export `SIFT_PARSE_ENGINE=digital-only` for the worker, and `SIFT_CHAT_BASE_URL=http://127.0.0.1:11434/v1` for chat.
4. Run `make migrate`, then `make demo`. The seed script does not start Compose.
5. Open the printed login URL, paste the API key, ask the printed questions.

Playwright `next build` and `next dev` must not share the same `apps/web/.next`. Record against `next dev` on :3000 after `rm -rf apps/web/.next`, or the Compose-mapped :3001 host port — never both on one `.next` tree.

