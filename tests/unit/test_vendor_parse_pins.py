"""Vendored sift-parse version pins (CVE-safe floors)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor" / "sift-parse"


def _version(pyproject: Path) -> str:
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'(?m)^version = "([^"]+)"', text)
    assert match, f"version missing in {pyproject}"
    return match.group(1)


def _name(pyproject: Path) -> str:
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'(?m)^name = "([^"]+)"', text)
    assert match, f"name missing in {pyproject}"
    return match.group(1)


def test_vendor_distribution_names_are_sift_prefixed() -> None:
    assert _name(VENDOR / "sift-parse" / "pyproject.toml") == "sift-parse"
    assert _name(VENDOR / "sift-parse-core" / "pyproject.toml") == "sift-parse-core"
    assert _name(VENDOR / "sift-parse-models" / "pyproject.toml") == "sift-parse-models"
    assert _name(VENDOR / "sift-parse-pdf" / "pyproject.toml") == "sift-parse-pdf"


def test_core_version_meets_cve_floor() -> None:
    version = _version(VENDOR / "sift-parse-core" / "pyproject.toml")
    major, minor, patch = (int(p) for p in version.split(".")[:3])
    assert (major, minor, patch) >= (2, 74, 1)


def test_parse_version_meets_phase0_floor() -> None:
    version = _version(VENDOR / "sift-parse" / "pyproject.toml")
    major, minor, patch = (int(p) for p in version.split(".")[:3])
    assert (major, minor, patch) >= (2, 94, 0)


def test_ingest_distribution_name_and_version() -> None:
    ingest = ROOT / "vendor" / "sift-ingest" / "pyproject.toml"
    assert _name(ingest) == "sift-ingest"
    assert _version(ingest) == "0.1.5"
