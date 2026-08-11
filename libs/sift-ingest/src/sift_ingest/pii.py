"""Presidio PII detection for ingest blocks (Phase 2 §2 step 9).

``pii_map`` stores entity type + character offsets + score only — never raw
PII values (``rules/code-security.mdc`` §6).
"""

from __future__ import annotations

from sift_core.models import Block


def detect_pii(text: str) -> dict[str, object] | None:
    """Scan ``text`` and return an offsets-only ``pii_map``, or ``None``.

    TDD stub — real Presidio Analyzer lands in the impl commit.
    """
    del text
    return None


def annotate_blocks_with_pii(blocks: list[Block]) -> list[Block]:
    """Return blocks with ``pii_map`` filled from ``detect_pii``.

    TDD stub — no-op until the impl commit.
    """
    return list(blocks)
