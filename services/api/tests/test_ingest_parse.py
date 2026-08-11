"""Unit tests for ingest status routing helpers."""

from __future__ import annotations

import pytest

from sift.parse import DigitalPdfParser, StandardPdfParser
from sift.parse.adapter import DocumentMetadata, Page, ParseResult
from sift_api.ingest_parse import (
    document_quality_score,
    document_status_after_parse,
    enrich_parse_result_with_pii,
    select_parser,
)
from sift_api.storage import parse_seaweed_uri
from sift_core.ids import IdKind, new_id
from sift_core.models import (
    Block,
    BlockType,
    BoundingBox,
    Provenance,
    ReviewState,
)


def _block(state: ReviewState, *, confidence: float = 0.99, ordinal: int = 0) -> Block:
    return Block(
        id=new_id(IdKind.BLOCK),
        ordinal=ordinal,
        block_type=BlockType.PARAGRAPH,
        text="hello",
        provenance=Provenance(
            page_no=1,
            bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            extractor="digital-pdf",
            model_version="pypdfium2",
        ),
        confidence=confidence,
        review_state=state,
    )


def test_document_status_indexing_when_all_approved() -> None:
    result = ParseResult(
        blocks=[_block(ReviewState.APPROVED)],
        metadata=DocumentMetadata(source_path="/tmp/x.pdf", page_count=1),
        pages=[Page(page_no=1, block_count=1)],
    )
    assert document_status_after_parse(result) == "indexing"


def test_document_status_ready_for_review_when_any_needs_review() -> None:
    result = ParseResult(
        blocks=[
            _block(ReviewState.APPROVED),
            Block(
                id=new_id(IdKind.BLOCK),
                ordinal=1,
                block_type=BlockType.PARAGRAPH,
                text="low",
                provenance=Provenance(
                    page_no=1,
                    bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
                    extractor="digital-pdf",
                    model_version="pypdfium2",
                ),
                confidence=0.4,
                review_state=ReviewState.NEEDS_REVIEW,
            ),
        ],
        metadata=DocumentMetadata(source_path="/tmp/x.pdf", page_count=1),
        pages=[Page(page_no=1, block_count=2)],
    )
    assert document_status_after_parse(result) == "ready_for_review"


def test_document_status_ready_for_review_when_policy_requires() -> None:
    result = ParseResult(
        blocks=[_block(ReviewState.APPROVED)],
        metadata=DocumentMetadata(source_path="/tmp/x.pdf", page_count=1),
        pages=[Page(page_no=1, block_count=1)],
    )
    assert document_status_after_parse(result, require_review=True) == "ready_for_review"


def test_document_quality_score_mean_for_small_n() -> None:
    result = ParseResult(
        blocks=[
            _block(ReviewState.APPROVED, confidence=0.8, ordinal=0),
            _block(ReviewState.APPROVED, confidence=1.0, ordinal=1),
        ],
        metadata=DocumentMetadata(source_path="/tmp/x.pdf", page_count=1),
        pages=[Page(page_no=1, block_count=2)],
    )
    assert document_quality_score(result) == 0.9


def test_document_quality_score_p10_for_n_ge_5() -> None:
    confidences = [0.1, 0.5, 0.6, 0.7, 0.9]
    blocks = [
        _block(ReviewState.NEEDS_REVIEW, confidence=c, ordinal=i) for i, c in enumerate(confidences)
    ]
    result = ParseResult(
        blocks=blocks,
        metadata=DocumentMetadata(source_path="/tmp/x.pdf", page_count=1),
        pages=[Page(page_no=1, block_count=5)],
    )
    score = document_quality_score(result)
    assert score is not None
    assert score == 0.1
    needs = sum(1 for b in result.blocks if b.review_state is ReviewState.NEEDS_REVIEW)
    assert needs == 5


def test_parse_seaweed_uri_splits_bucket_and_key() -> None:
    bucket, key = parse_seaweed_uri("seaweed://sift-uploads/t/tenant/d/doc/original.pdf")
    assert bucket == "sift-uploads"
    assert key == "t/tenant/d/doc/original.pdf"


def test_select_parser_defaults_to_standard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIFT_PARSE_ENGINE", raising=False)
    assert isinstance(select_parser(mime="application/pdf"), StandardPdfParser)


def test_select_parser_digital_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIFT_PARSE_ENGINE", "digital-only")
    assert isinstance(select_parser(mime="application/pdf"), DigitalPdfParser)


def test_enrich_parse_result_with_pii_populates_offsets_only() -> None:
    seeded = "Contact alice.secret@example.com for details."
    block = _block(ReviewState.APPROVED)
    block = block.model_copy(update={"text": seeded})
    result = ParseResult(
        blocks=[block],
        metadata=DocumentMetadata(source_path="/tmp/x.pdf", page_count=1),
        pages=[Page(page_no=1, block_count=1)],
    )
    enriched = enrich_parse_result_with_pii(result)
    assert enriched.blocks[0].pii_map is not None
    blob = str(enriched.blocks[0].pii_map)
    assert "alice.secret@example.com" not in blob


def test_enrich_parse_result_with_pii_swallows_scanner_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_blocks: object) -> list[object]:
        raise RuntimeError("scanner down")

    monkeypatch.setattr("sift_api.ingest_parse.annotate_blocks_with_pii", boom)
    result = ParseResult(
        blocks=[_block(ReviewState.APPROVED)],
        metadata=DocumentMetadata(source_path="/tmp/x.pdf", page_count=1),
        pages=[Page(page_no=1, block_count=1)],
    )
    out = enrich_parse_result_with_pii(result)
    assert out.blocks[0].pii_map is None
    assert out.blocks[0].text == "hello"
