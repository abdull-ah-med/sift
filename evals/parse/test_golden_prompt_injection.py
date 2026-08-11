"""Parse-quality golden: Prompt Injection paper (Liu et al., arXiv:2306.05499)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from sift.parse import ParseConfig, StandardPdfParser
from sift_core.models import BlockType, ReviewState

_FIXTURE = Path(__file__).resolve().parents[1] / "corpus" / "pdf" / "prompt_injection_liu_2023.pdf"
_SHA256 = "7671887b19dad8ac4d514a45b4701882575860530615edee560c495623064828"


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SIFT_HAVE_PARSE_WEIGHTS") != "1",
    reason="requires prefetched parse weights",
)
def test_golden_prompt_injection_structure() -> None:
    assert _FIXTURE.is_file(), f"missing fixture {_FIXTURE}"
    digest = hashlib.sha256(_FIXTURE.read_bytes()).hexdigest()
    assert digest == _SHA256

    # Threshold raised above this paper's layout floor (~0.85) so HITL fires;
    # product default stays 0.75 (plan: do not lower the product threshold).
    result = StandardPdfParser().parse(_FIXTURE, ParseConfig(confidence_threshold=0.90))
    assert result.metadata.page_count == 18
    assert len(result.blocks) > 18  # not one blob per page

    headings = sum(1 for b in result.blocks if b.block_type is BlockType.HEADING)
    tables = sum(1 for b in result.blocks if b.block_type is BlockType.TABLE)
    assert headings >= 8
    assert tables >= 3

    assert sum(1 for b in result.blocks if b.text and "\x02" in b.text) == 0
    # Longest natural paragraph on this paper is ~4.5k; page-blob mode was ~one
    # multi-KB block per page (18 blocks total). Cap still far below that mode.
    assert max((len(b.text or "") for b in result.blocks), default=0) < 5000

    assert any(b.review_state is ReviewState.NEEDS_REVIEW for b in result.blocks)
