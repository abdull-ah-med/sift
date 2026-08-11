# Model weight prefetch

`prefetch.py` downloads the HuggingFace snapshots the vendored
`StandardPdfPipeline` needs **before** request time. Product parse paths must
not hit the Hub on a user request; missing weights raise
`sift.parse.MissingModelWeightsError`.

## Default plan (digital PDF)

| Role | HuggingFace repo | Revision |
|---|---|---|
| layout | `docling-project/docling-layout-heron` | `main` |
| layout-onnx | `docling-project/docling-layout-heron-onnx` | `main` |
| tableformer | `docling-project/docling-models` | `v2.3.0` |

OCR is **opt-in** (`--with-ocr`). That adds `nvidia/nemotron-ocr-v2` (HF-hosted
OCR path in the engine). RapidOCR / EasyOCR use non-HF downloaders; pull those
via the engine's `download_models(...)` helpers if you enable those OCR backends.

## Usage

```bash
# Print the plan (no network)
uv run python tools/models/prefetch.py --dry-run

# Populate ~/.cache/sift/models/ (or $HF_HOME if set)
uv run python tools/models/prefetch.py

# Custom cache root
uv run python tools/models/prefetch.py --cache-dir /var/cache/sift/models

# Include OCR weights
uv run python tools/models/prefetch.py --with-ocr
```

`tools/dev/setup.sh` runs the default prefetch after `uv sync`.

CI runs prefetch and exports `SIFT_HAVE_PARSE_WEIGHTS=1` so integration /
golden tests may assume the cache is warm.

## Air-gapped / offline

1. On a networked machine: `prefetch.py --cache-dir ./models-bundle`
2. Copy `./models-bundle` (including `manifest.json`) onto the offline host
3. Point `HF_HOME` (or `--cache-dir`) at that directory
4. Do **not** enable request-time Hub download in product code

## Cache layout

Each repo is stored as `{cache}/{owner}--{name}/` (engine-compatible) plus a
top-level `manifest.json` listing role, repo_id, revision, and path.
