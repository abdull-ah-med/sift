# sift

Privacy-first document intelligence, RAG, and agent knowledge base — self-hostable, air-gap capable, minimally opinionated about your models.

Point sift at a folder of documents. Get back a searchable, chattable, agent-ready knowledge base with citations, review workflows, and a first-class MCP interface for LLM agents.

Status: **pre-alpha, in active development.** This repository is intentionally near-empty at the top level while the product is being built. Public artifacts will land here as they stabilize.

---

## What sift does

- **Ingest** — PDF, DOCX, PPTX, XLSX, CSV, HTML, images. Layout-aware extraction with confidence scores and human-in-the-loop review.
- **Retrieve** — hybrid dense + BM25 retrieval with reranking, grounded in your documents.
- **Chat** — streamed answers with source citations, session memory, and verification.
- **Serve agents** — a first-class MCP endpoint (`/mcp`) plus a REST mirror. Give any agent scoped, auditable access to your knowledge.
- **Vault** — a markdown vault with wikilinks, backlinks, tags, and a graph view.
- **Everywhere** — CLI, web app, and Docker Compose. Kubernetes and air-gap installers on the roadmap.

---

## Getting started

```bash
./tools/dev/setup.sh   # or: make setup
make test
```

Docker Compose, API, and workers land in later Phase 0 PRs.

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
- `tools/` — setup, migrations, model prefetch

---

## Contributing

Not accepting external contributions yet. Watch this space.

---

## License

[Apache License 2.0](./LICENSE) · Copyright © 2026 Abdullah Ahmed

---

**Author:** Abdullah Ahmed · [contactabdullahahmed@gmail.com](mailto:contactabdullahahmed@gmail.com) · [@abdull-ah-med](https://github.com/abdull-ah-med) · [github.com/abdull-ah-med/sift](https://github.com/abdull-ah-med/sift)
