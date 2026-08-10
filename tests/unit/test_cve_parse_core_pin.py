"""P6 — vendored sift-parse-core is above CVE-2026-44023 floor."""

from __future__ import annotations

import re
from pathlib import Path

CORE = Path(__file__).resolve().parents[2] / "vendor/sift-parse/sift-parse-core/pyproject.toml"
# Affected range documented as >=1.5.0,<2.74.1
FLOOR = (2, 74, 1)


def test_sift_parse_core_version_above_cve_floor() -> None:
    text = CORE.read_text(encoding="utf-8")
    match = re.search(r'(?m)^version = "([^"]+)"', text)
    assert match, "version missing"
    parts = tuple(int(p) for p in match.group(1).split(".")[:3])
    assert parts >= FLOOR


def test_sanitize_helpers_present_in_vendored_core() -> None:
    """Patched helpers from the CVE fix lineage must exist in the vendored tree."""
    root = CORE.parent
    hits = list(root.rglob("*.py"))
    blob = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in hits)
    assert "_is_safe_url" in blob or "is_safe_url" in blob or "sanitize" in blob.lower()
