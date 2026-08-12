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
| `docling` | `sift_parse` | `sift-parse-engine` |
| `docling_core` | `sift_parse_core` | `sift-parse-core-engine` |
| `docling_parse` | `sift_parse_pdf` | `sift-parse-pdf-engine` |
| `docling_ibm_models` | `sift_parse_models` | `sift-parse-models-engine` |

Dist names use the `-engine` suffix so they do not collide with the product adapter
package `libs/sift-parse` (`name = "sift-parse"`). Import roots stay unchanged (ADR-0011).

Product code imports **`sift.parse`** (adapter). Services must not import `vendor/` directly.

Do **not** rename Hugging Face `repo_id` strings that still point at `docling-project/…` artifacts — those are upstream weight coordinates.

## CVE pins

- `sift-parse-core-engine` must stay **≥ 2.74.1** (CVE-2026-44023 / GHSA lineage: SSRF + `Content-Disposition` path traversal).
- `sift-parse-engine` must stay on a release that depends on the patched core (≥ **2.94.0** lineage; currently **2.119.0**).

## Distribution rename

PyPI / hatch `name` fields in each tree are renamed to `sift-parse*-engine` so they do not collide with the product adapter dist `sift-parse` (`libs/sift-parse`) and so an accidental `uv add docling` cannot silently replace the vendored package.

## Vendored native artifacts

`sift-parse-pdf` is a hybrid Python + C++ (pybind11) package. Upstream ships `pdf_parsers` only inside built wheels — never in the source tree. Source-only vendoring therefore drops the module every PDF backend imports. Per ADR-0015 we vendor the pinned-wheel `.so` files (git-lfs) until a CMake/QPDF build plan lands.

| File path | Platform triple | Upstream wheel URL | Wheel SHA256 | Extracted `.so` SHA256 |
|---|---|---|---|---|
| `sift-parse-pdf/docling_parse/pdf_parsers.cpython-313-darwin.so` | `aarch64-apple-darwin` | https://files.pythonhosted.org/packages/c6/84/614a3b6b4c0263fc8d06a24ae03fe75d438c431bc525b4b71ce7a011923a/docling_parse-7.11.0-cp313-cp313-macosx_14_0_arm64.whl | `4a339f8e6a15bf13359359d2ad236b4bb1c6bf51d606ba4ce03cbaeddc60d579` | `68ed665a8a52a653f2bcff7753668be305eeb440bc6f65212db3e12a752c2f8b` |
| `sift-parse-pdf/docling_parse/pdf_parsers.cpython-313-x86_64-linux-gnu.so` | `x86_64-unknown-linux-gnu` | https://files.pythonhosted.org/packages/61/0e/0bc5b01967ad16c88766ffc72ac42e6deeeb160e734f1b7f383c746a082a/docling_parse-7.11.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl | `94faec9b76e8c65c7e5aeeb20004aa9703fb78c3cf52bac2ee8dd155569f22e7` | `a704c4cb9c7cf9e55293655f33a989249a5e6b5acd3ac6a73cc50336f9b4ffa5` |

Verify (from repo root):

```bash
shasum -a 256 vendor/sift-parse/sift-parse-pdf/docling_parse/pdf_parsers.cpython-313-darwin.so
shasum -a 256 vendor/sift-parse/sift-parse-pdf/docling_parse/pdf_parsers.cpython-313-x86_64-linux-gnu.so
```

Refresh: re-download the two `docling-parse==7.11.0` cp313 wheels above, extract
`docling_parse/pdf_parsers.cpython-313-*.so` **and** `docling_parse/pdf_resources/`,
keep the upstream package dir name `docling_parse/` (the `.so` hardcodes that resource
path), leave the Python API under `sift_parse_pdf/`, update this table’s SHA256 columns,
then re-run the verify commands.

**Note:** The pybind11 extension must be imported as `docling_parse.pdf_parsers`. Loading
the same `.so` as `sift_parse_pdf.pdf_parsers` segfaults on construct. `sift_parse_pdf`
stays the product-facing import root and pulls the extension from `docling_parse`.

## Slimming

Trees keep **runtime sources only** (plus the native artifacts table above). After verifying a pin, delete upstream `tests/` / `test/`, `docs/`, `examples/`, lockfiles, and CI meta so the monorepo stays reviewable.

Verification (2026-08-10) against shallow clones of the pins above:

| Upstream | Result |
|---|---|
| `docling-core` `v2.91.0` | **589 passed**, 6 skipped |
| `LongParser` `v0.1.5` (absorbed) | Patterns live in `libs/sift-ingest/` / `libs/sift-parse/` |
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
