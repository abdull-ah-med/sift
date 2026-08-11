"""Failing-first tests for Block domain models (Phase 2)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from sift_core.ids import IdKind, new_id, validate_id
from sift_core.models import (
    Block,
    BlockType,
    BoundingBox,
    Provenance,
    ReviewState,
    review_state_for_confidence,
)


def test_block_requires_provenance_and_typed_id() -> None:
    block_id = new_id(IdKind.BLOCK)
    block = Block(
        id=block_id,
        ordinal=0,
        block_type=BlockType.PARAGRAPH,
        text="Hello sift",
        provenance=Provenance(
            page_no=1,
            bbox=BoundingBox(x0=0.0, y0=0.0, x1=10.0, y1=20.0),
            extractor="digital-pdf",
            model_version="pypdfium2",
        ),
        confidence=0.98,
        review_state=ReviewState.APPROVED,
    )

    assert validate_id(block.id, IdKind.BLOCK) == block_id
    assert block.version == 1
    assert block.provenance.page_no == 1
    assert block.review_state is ReviewState.APPROVED


def test_block_rejects_unknown_review_state() -> None:
    with pytest.raises(ValidationError):
        Block(
            id=new_id(IdKind.BLOCK),
            ordinal=0,
            block_type=BlockType.PARAGRAPH,
            text="x",
            provenance=Provenance(
                page_no=1,
                bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
                extractor="digital-pdf",
                model_version="pypdfium2",
            ),
            review_state="bogus",  # type: ignore[arg-type]
        )


def test_low_confidence_defaults_to_needs_review_helper() -> None:
    assert review_state_for_confidence(0.5, threshold=0.75) is ReviewState.NEEDS_REVIEW
    assert review_state_for_confidence(0.9, threshold=0.75) is ReviewState.APPROVED
