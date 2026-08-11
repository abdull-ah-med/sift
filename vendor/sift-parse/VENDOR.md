# Vendored sift-parse stack

Sift-owned copies of the document-parsing engine. **Do not** `pip install` upstream
distributions in product code — import via the product adapter `sift.parse`
(`libs/sift-parse`), which may load the vendored engine modules below.

## Upstream map

| Directory | Upstream | Tag / commit | SPDX |
|---|---|---|---|
| `sift-parse/` | [docling-project/docling](https://github.com/docling-project/docling) | `v2.119.0` (`632f00c1`) | MIT |
| `sift-parse-core/` | [docling-project/docling-core](https://github.com/docling-project/docling-core) | `v2.91.0` | MIT |
| `sift-parse-models/` | [docling-project/docling-ibm-models](https://github.com/docling-project/docling-ibm-models) | `v3.13.3` | MIT |
| `sift-parse-pdf/` | [docling-project/docling-parse](https://github.com/docling-project/docling-parse) | `v7.11.0` | MIT |

Product / internal name: **sift-parse**. Upstream brand names stay in this file, `LICENSES/`, and `NOTICES.md` only.

## Import roots (ADR-0011)

| Upstream import root | Vendored import root | Dist name |
|---|---|---|
| `docling` | `sift_parse` | `sift-parse` |
| `docling_core` | `sift_parse_core` | `sift-parse-core` |
| `docling_parse` | `sift_parse_pdf` | `sift-parse-pdf` |
| `docling_ibm_models` | `sift_parse_models` | `sift-parse-models` |

Product code imports **`sift.parse`** (adapter). Services must not import `vendor/` directly.

Do **not** rename Hugging Face `repo_id` strings that still point at `docling-project/…` artifacts — those are upstream weight coordinates.

## CVE pins

- `sift-parse-core` must stay **≥ 2.74.1** (CVE-2026-44023 / GHSA lineage: SSRF + `Content-Disposition` path traversal).
- `sift-parse` must stay on a release that depends on the patched core (≥ **2.94.0** lineage; currently **2.119.0**).

## Distribution rename

PyPI / hatch `name` fields in each tree are renamed to `sift-parse*` so an accidental `uv add docling` cannot silently replace the vendored package.

## Slimming

Trees keep **runtime sources only**. After verifying a pin, delete upstream `tests/` / `test/`, `docs/`, `examples/`, lockfiles, and CI meta so the monorepo stays reviewable.

Verification (2026-08-10) against shallow clones of the pins above:

| Upstream | Result |
|---|---|
| `docling-core` `v2.91.0` | **589 passed**, 6 skipped |
| `LongParser` `v0.1.5` (`tests/unit`) | **58 passed** (see `../sift-ingest/VENDOR.md`) |
| `docling` / `docling-parse` / `docling-ibm-models` | Packages built at pin; full engine pytest deferred (optional extras / ML) — sift parse-smoke + core suite cover Phase 0 |

## Refresh procedure

1. Identify the upstream tag (or commit) to pull.
2. Shallow-clone upstream; run its test suite there.
3. Copy runtime sources into this tree (no nested `.git`); strip tests/docs/examples again.
4. Re-apply the distribution rename (`sift-parse*` names in `pyproject.toml`).
5. Re-apply the **import-root rename** (ADR-0011): rename package dirs and rewrite import roots (`docling`→`sift_parse`, `docling_core`→`sift_parse_core`, `docling_parse`→`sift_parse_pdf`, `docling_ibm_models`→`sift_parse_models`). Preserve upstream GitHub URLs under `docling-project/…` and Hugging Face `repo_id` strings. Rename any new `*docling_parse*_backend.py` modules to `sift_parse_pdf*_backend.py`. Do **not** leave one-shot rewrite scripts in the tree.
6. Run sift pytest: CVE pin (P6) + parse-smoke + `tests/unit/test_vendor_import_roots.py`.
7. Update this file’s tag/commit table and `NOTICES.md`.

## Owner

Abdullah Ahmed (`abdull-ah-med`)

## Date vendored

2026-08-10

## Import-path modernization

2026-08-11 — ADR-0011 applied on `feature/phase-0` (Phase 0 closeout).
