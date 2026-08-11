"""Failing-first tests for sift.parse Parser protocol (Phase 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sift.parse import DigitalPdfParser, ParseConfig, ParseResult
from sift_core.models import BlockType, ReviewState

CORPUS = Path(__file__).resolve().parents[3] / "evals" / "corpus"
DIGITAL_PDFS = sorted(CORPUS.glob("digital-*.pdf"))


def test_digital_parser_returns_ordered_blocks_for_corpus_pdf() -> None:
    assert DIGITAL_PDFS, "expected digital-*.pdf fixtures under evals/corpus"
    pdf = DIGITAL_PDFS[0]
    result = DigitalPdfParser().parse(pdf, ParseConfig())

    assert isinstance(result, ParseResult)
    assert result.blocks, "expected at least one block"
    assert [b.ordinal for b in result.blocks] == list(range(len(result.blocks)))
    assert all(b.block_type is BlockType.PARAGRAPH for b in result.blocks)
    assert all(b.text and b.text.strip() for b in result.blocks)
    assert all(b.provenance.extractor == "digital-pdf" for b in result.blocks)
    assert all(b.provenance.page_no >= 1 for b in result.blocks)
    assert result.metadata.page_count >= 1
    assert result.metadata.source_path == str(pdf.resolve())


def test_digital_parser_raises_when_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.pdf"
    with pytest.raises(FileNotFoundError):
        DigitalPdfParser().parse(missing, ParseConfig())


def test_parse_config_disables_url_fetch_by_default() -> None:
    config = ParseConfig()
    assert config.allow_url_fetch is False
    assert config.confidence_threshold == ParseConfig.model_fields["confidence_threshold"].default


def test_digital_parser_assigns_review_state_from_threshold() -> None:
    pdf = DIGITAL_PDFS[0]
    # Digital extraction is high-confidence; force a high threshold so all need review.
    result = DigitalPdfParser().parse(pdf, ParseConfig(confidence_threshold=1.01))
    assert all(b.review_state is ReviewState.NEEDS_REVIEW for b in result.blocks)
