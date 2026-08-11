"""Prefetch HuggingFace weights needed by the vendored StandardPdfPipeline.

Downloads happen only here (dev setup / CI). Product parse paths must refuse
request-time Hub downloads and raise ``MissingModelWeightsError`` instead.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from huggingface_hub import snapshot_download

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    help="Prefetch parse-model weights into the local cache.",
)


@dataclass(frozen=True)
class PrefetchItem:
    """One HuggingFace snapshot to materialize under the cache root."""

    repo_id: str
    revision: str
    role: str


# Layout + TableFormer (V1) — required for StandardPdfPipeline digital PDFs.
_REQUIRED: tuple[PrefetchItem, ...] = (
    PrefetchItem("docling-project/docling-layout-heron", "main", "layout"),
    PrefetchItem(
        "docling-project/docling-layout-heron-onnx",
        "main",
        "layout-onnx",
    ),
    PrefetchItem("docling-project/docling-models", "v2.3.0", "tableformer"),
)

# OCR is opt-in: digital PDFs usually skip it. Nemotron is the HF-hosted OCR
# path wired in the vendored engine; RapidOCR/EasyOCR use non-HF downloaders.
_OCR: tuple[PrefetchItem, ...] = (PrefetchItem("nvidia/nemotron-ocr-v2", "main", "ocr"),)


def build_prefetch_plan(*, with_ocr: bool = False) -> list[PrefetchItem]:
    """Return the ordered list of Hub snapshots to cache."""
    plan = list(_REQUIRED)
    if with_ocr:
        plan.extend(_OCR)
    return plan


def resolve_cache_dir(explicit: Path | None = None) -> Path:
    """Resolve cache root: ``--cache-dir``, else ``$HF_HOME``, else ``~/.cache/sift/models``."""
    if explicit is not None:
        return explicit.expanduser().resolve()
    if hf_home := os.environ.get("HF_HOME"):
        return Path(hf_home).expanduser().resolve()
    return (Path.home() / ".cache" / "sift" / "models").resolve()


def _local_dir(cache_dir: Path, repo_id: str) -> Path:
    return cache_dir / repo_id.replace("/", "--")


def _write_manifest(cache_dir: Path, entries: list[dict[str, str]]) -> None:
    path = cache_dir / "manifest.json"
    path.write_text(
        json.dumps({"models": entries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_prefetch(
    cache_dir: Path,
    plan: list[PrefetchItem],
    *,
    dry_run: bool,
    force: bool,
) -> list[dict[str, str]]:
    """Materialize ``plan`` under ``cache_dir``; return manifest rows."""
    entries: list[dict[str, str]] = []
    for item in plan:
        dest = _local_dir(cache_dir, item.repo_id)
        row = {
            "role": item.role,
            "repo_id": item.repo_id,
            "revision": item.revision,
            "path": str(dest),
        }
        entries.append(row)
        typer.echo(
            f"{item.role}: {item.repo_id}@{item.revision} -> {dest}"
            + (" (dry-run)" if dry_run else "")
        )
        if dry_run:
            continue
        cache_dir.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=item.repo_id,
            revision=item.revision,
            local_dir=str(dest),
            force_download=force,
        )
    if not dry_run:
        _write_manifest(cache_dir, entries)
    return entries


@app.callback(invoke_without_command=True)
def _cli(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the plan; do not touch the network."),
    ] = False,
    cache_dir: Annotated[
        Path | None,
        typer.Option(
            "--cache-dir",
            help="Override cache root (default: HF_HOME or ~/.cache/sift/models).",
        ),
    ] = None,
    with_ocr: Annotated[
        bool,
        typer.Option("--with-ocr", help="Also prefetch HF-hosted OCR weights."),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", help="Re-download even when the local snapshot exists."),
    ] = False,
) -> None:
    root = resolve_cache_dir(cache_dir)
    plan = build_prefetch_plan(with_ocr=with_ocr)
    run_prefetch(root, plan, dry_run=dry_run, force=force)


def main(argv: list[str] | None = None) -> int:
    """Entry point used by tests and ``uv run python tools/models/prefetch.py``."""
    try:
        app(args=argv, standalone_mode=False)
    except typer.Exit as exc:
        return int(exc.exit_code or 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
