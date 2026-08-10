# Vendored sift-ingest

Sift-owned copy of **LongParser** (ENDEVSOLS). Absorbed into `libs/sift-*` by end of Phase 2; this tree is transitional.

## Upstream

| Field | Value |
|---|---|
| Upstream | https://github.com/ENDEVSOLS/LongParser |
| Tag / commit | `v0.1.5` / `58c688f28c92f751f81d93f30673a22bec7fb6f2` |
| SPDX | MIT (see tree `LICENSE` / third-party notices) |
| Vendored | 2026-08-10 |

Product name: **sift-ingest**. Upstream org attribution only in `LICENSES/` and `NOTICES.md`.

## Immediate follow-ups (Phase 0–2)

- Strip Mongo / ARQ dependencies; rewrite to Postgres + Taskiq + Valkey (Phase 2).
- Point extractors at vendored `sift-parse` (not PyPI docling).
- Rename `LONGPARSER_*` env vars to `SIFT_INGEST_*` as code is absorbed.

## Refresh procedure

1. Pull upstream tag into a temp shallow clone.
2. Replace this directory (no nested `.git`).
3. Re-apply `name = "sift-ingest"` and any sift patches.
4. Run ingest unit tests + Phase 0 spikes that touch extract.

## Owner

Abdullah Ahmed (`abdull-ah-med`)
