# sift

Privacy-first document intelligence that runs on your machine. Ingest PDFs, review low-confidence extracts, search with citations, and ask questions against your own documents.

Status: **pre-alpha.** Phase 4 is in progress on `dev`. MCP, vault, and hosted SaaS are not in this tree yet.

---

## What sift does

- **Ingest** — PDFs go through layout-aware extraction with confidence scores. Clean digital files skip review and become searchable; flagged blocks wait in a review queue.
- **Retrieve** — hybrid search over your chunks, with optional rerank.
- **Chat** — streamed answers with source citations. Local OpenAI-compatible models (Ollama on loopback) or a cloud key you supply.
- **Review** — human-in-the-loop edits before a document is indexed.

---

## Local demo

You need Docker, a local Ollama install, and enough RAM for Postgres plus embeddings plus a small instruct model.

```bash
# Core services, then embeddings (ml profile). Apple Silicon: set SIFT_TEI_IMAGE
# to the arm64 digest in deploy/compose/README.md.
docker compose -f deploy/compose/dev.yml --profile ml up -d

ollama pull llama3.1
export SIFT_PARSE_ENGINE=digital-only
export SIFT_CHAT_BASE_URL=http://127.0.0.1:11434/v1
export SIFT_API_KEY_PEPPER=dev-pepper-change-me   # match .env; do not commit .env

make migrate
make demo
make web
```

Open the printed login URL (`http://127.0.0.1:3000/login`), paste the printed API key, open the `demo` collection, and ask the two printed questions. Details and the Playwright vs `next dev` warning: `deploy/compose/README.md`.

`make demo` does not start Compose. First run prints a bootstrap key once; later runs need `SIFT_DEMO_API_KEY` set to that key.

---

## Getting started (dev)

```bash
./tools/dev/setup.sh   # or: make setup
make test
```

---

## Repository layout

- `apps/` — web (Next.js) and CLI
- `services/` — API, workers, MCP proxy
- `libs/` — sift-owned Python libraries
- `vendor/` — vendored parse/ingest baselines (sift-owned forks)
- `packages/` — shared TypeScript packages
- `deploy/` — Compose profiles, Helm, Ansible
- `evals/` — corpora, goldens, spikes, eval reports
- `tests/` — integration, e2e, fixtures
- `tools/` — setup, migrations, model prefetch, demo seed

---

## Contributing

Not accepting external contributions yet.

---

## License

[Apache License 2.0](./LICENSE) · Copyright © 2026 Abdullah Ahmed

---

**Author:** Abdullah Ahmed · [contactabdullahahmed@gmail.com](mailto:contactabdullahahmed@gmail.com) · [@abdull-ah-med](https://github.com/abdull-ah-med) · [github.com/abdull-ah-med/sift](https://github.com/abdull-ah-med/sift)
