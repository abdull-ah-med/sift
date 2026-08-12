"""Phase 2 §5: vendor/sift-ingest absorbed into libs/sift-*; vendor tree gone."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# §5 destination is libs/sift-ingest; §10 docs-only is relaxed for first-party
# package name, workspace wiring, Docker COPY paths, and license notices.
_ALLOW_HYPHEN = re.compile(
    r"^(docs/|LICENSES/|NOTICES\.md$|CHANGELOG\.md$|libs/sift-ingest/|"
    r"libs/sift-ingest\.README\.md$|"
    r"services/.*/Dockerfile$|Makefile$|pyproject\.toml$|"
    r"services/api/pyproject\.toml$|\.gitleaks\.toml$|"
    r"uv\.lock$|tests/unit/test_sift_ingest_absorbed\.py$|"
    r"tests/unit/test_vendor_parse_pins\.py$|"
    r"vendor/sift-parse/VENDOR\.md$)"
)

_REQUIRED_MODULES = (
    "sift_ingest.equation_flags",
    "sift_ingest.semantic_boundary",
    "sift_ingest.quality_scorer",
    "sift_ingest.orchestrator",
    "sift_ingest.cross_reference",
    "sift_ingest.summary_enricher",
    "sift_ingest.utils.lang_detect",
    "sift_ingest.utils.rtl_detector",
    "sift_ingest.utils.ocr_router",
    "sift.parse.base",
    "sift.parse.adapters.formula_ocr",
    "sift.parse.adapters.sift_parse_standard",
)


def test_vendor_sift_ingest_directory_deleted() -> None:
    assert not (ROOT / "vendor" / "sift-ingest").exists()


def test_absorbed_modules_importable() -> None:
    for name in _REQUIRED_MODULES:
        importlib.import_module(name)


def test_no_longparser_imports_outside_docs_and_licenses() -> None:
    offenders: list[str] = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(("vendor/", ".venv/", "node_modules/", ".sift-local/")):
            continue
        if rel.startswith("docs/") or rel.startswith("LICENSES/"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "longparser" in text or "from sift_ingest_vendor" in text:
            offenders.append(rel)
    assert not offenders, "longparser residue:\n" + "\n".join(offenders[:40])


def test_hyphen_sift_ingest_only_in_allowed_paths() -> None:
    """§10 wants docs-only; plan allows licenses + first-party libs/sift-ingest."""
    offenders: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(
            (
                ".git/",
                ".venv/",
                "node_modules/",
                ".sift-local/",
                "vendor/sift-parse/",
                "evals/reports/",
            )
        ):
            continue
        if path.suffix not in {".py", ".md", ".toml", ".yml", ".yaml", ".txt", ".lock", ""}:
            if path.name not in {"Dockerfile", "Makefile"}:
                continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "sift-ingest" not in text and "sift-ingest" not in rel:
            continue
        if "sift-ingest" in rel or "sift-ingest" in text:
            if _ALLOW_HYPHEN.match(rel):
                continue
            offenders.append(rel)
    assert not offenders, "unexpected sift-ingest references:\n" + "\n".join(offenders[:40])
