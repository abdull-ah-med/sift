"""Unit tests for ingest status routing helpers."""

from __future__ import annotations

from sift.parse.adapter import DocumentMetadata, Page, ParseResult
from sift_api.ingest_parse import document_status_after_parse
from sift_api.storage import parse_seaweed_uri
from sift_core.ids import IdKind, new_id
from sift_core.models import (
    Block,
    BlockType,
    BoundingBox,
    Provenance,
    ReviewState,
)


def _block(state: ReviewState) -> Block:
    return Block(
        id=new_id(IdKind.BLOCK),
        ordinal=0,
        block_type=BlockType.PARAGRAPH,
        text="hello",
        provenance=Provenance(
            page_no=1,
            bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            extractor="digital-pdf",
            model_version="pypdfium2",
        ),
        confidence=0.99,
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


def test_parse_seaweed_uri_splits_bucket_and_key() -> None:
    bucket, key = parse_seaweed_uri("seaweed://sift-uploads/t/tenant/d/doc/original.pdf")
    assert bucket == "sift-uploads"
    assert key == "t/tenant/d/doc/original.pdf"
