"""Guard: vendored trees must not keep upstream Docling import roots.

Exception (VENDOR.md): the pybind11 ``pdf_parsers`` extension hardcodes the
upstream package path ``docling_parse`` for ``pdf_resources``. Product code
imports via ``sift_parse_pdf``; only that shim may import ``docling_parse``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VENDOR_ROOTS = [
    ROOT / "vendor" / "sift-parse",
]

# Import forms that prove the tree still teaches engineers to use upstream names.
FORBIDDEN = re.compile(
    r"(?m)^\s*(?:from|import)\s+("
    r"docling\b|docling_core\b|docling_parse\b|docling_ibm_models\b"
    r")"
)

# Allowed solely for the native extension resource path (see VENDOR.md).
_ALLOWED_DOCLING_PARSE_IMPORT = (
    ROOT / "vendor/sift-parse/sift-parse-pdf/sift_parse_pdf/pdf_parser.py"
)
_ALLOWED_DOCLING_PARSE_DIR = ROOT / "vendor/sift-parse/sift-parse-pdf/docling_parse"

TEXT_SUFFIXES = {".py", ".pyi"}


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in VENDOR_ROOTS:
        if not root.is_dir():
            continue
        files.extend(p for p in root.rglob("*") if p.suffix in TEXT_SUFFIXES and p.is_file())
    return files


def test_vendor_trees_have_no_upstream_docling_imports() -> None:
    offenders: list[str] = []
    for path in _iter_python_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in FORBIDDEN.finditer(text):
            root_name = match.group(1)
            if (
                root_name == "docling_parse"
                and path.resolve() == _ALLOWED_DOCLING_PARSE_IMPORT.resolve()
            ):
                continue
            rel = path.relative_to(ROOT)
            offenders.append(f"{rel}: import root `{root_name}`")
    assert not offenders, "upstream import roots remain:\n" + "\n".join(offenders[:50])


@pytest.mark.parametrize(
    ("old_name", "new_dir"),
    [
        ("docling", "sift_parse"),
        ("docling_core", "sift_parse_core"),
        ("docling_parse", "sift_parse_pdf"),
        ("docling_ibm_models", "sift_parse_models"),
    ],
)
def test_vendor_package_directories_use_sift_names(old_name: str, new_dir: str) -> None:
    parse_root = ROOT / "vendor" / "sift-parse"
    leftover = [
        p
        for p in parse_root.rglob(old_name)
        if p.is_dir() and p.name == old_name and p.resolve() != _ALLOWED_DOCLING_PARSE_DIR.resolve()
    ]
    assert not leftover, f"old directory name still present: {old_name} → {leftover[:5]}"
    if old_name == "docling_parse":
        assert _ALLOWED_DOCLING_PARSE_DIR.is_dir(), "expected native docling_parse shim dir"
    matches = [p for p in parse_root.rglob(new_dir) if p.is_dir() and p.name == new_dir]
    assert matches, f"expected vendored package directory {new_dir}"
