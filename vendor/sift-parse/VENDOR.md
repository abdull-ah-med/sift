# Vendored sift-parse stack

Sift-owned copies of the Docling document-parsing stack. **Do not** `pip install docling` / `docling-core` in product code — import these trees (or the `libs/sift-parse` adapter).

## Upstream map

| Directory | Upstream | Tag / commit | SPDX |
|---|---|---|---|
| `sift-parse/` | [docling-project/docling](https://github.com/docling-project/docling) | `v2.119.0` (`632f00c1`) | MIT |
| `sift-parse-core/` | [docling-project/docling-core](https://github.com/docling-project/docling-core) | `v2.91.0` | MIT |
| `sift-parse-models/` | [docling-project/docling-ibm-models](https://github.com/docling-project/docling-ibm-models) | `v3.13.3` | MIT |
| `sift-parse-pdf/` | [docling-project/docling-parse](https://github.com/docling-project/docling-parse) | `v7.11.0` | MIT |

Product / internal name: **sift-parse**. Upstream brand names stay in this file, `LICENSES/`, and `NOTICES.md` only.

## CVE pins

- `sift-parse-core` must stay **≥ 2.74.1** (CVE-2026-44023 / GHSA lineage: SSRF + `Content-Disposition` path traversal).
- `sift-parse` must stay on a release that depends on the patched core (≥ **2.94.0** lineage; currently **2.119.0**).

## Distribution rename

PyPI / hatch `name` fields in each tree are renamed to `sift-parse*` so an accidental `uv add docling` cannot silently replace the vendored package.

## Refresh procedure

1. Identify the upstream tag (or commit) to pull.
2. Replace the matching directory contents (prefer shallow clone + copy; avoid re-introducing nested `.git`).
3. Re-apply the distribution rename and any sift patches (see git history under `vendor/sift-parse/`).
4. Run unit tests + spike P6 (CVE regression) + parse-smoke.
5. Update this file’s tag/commit table and `NOTICES.md`.

## Owner

Abdullah Ahmed (`abdull-ah-med`)

## Date vendored

2026-08-10
