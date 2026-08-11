"""Tests for Phase 2 block chunker."""

from __future__ import annotations

from sift_core.ids import IdKind, new_id
from sift_core.models import (
    Block,
    BlockType,
    BoundingBox,
    Provenance,
    ReviewState,
)
from sift_ingest.chunker import chunk_blocks


def _block(
    *,
    ordinal: int,
    text: str,
    state: ReviewState = ReviewState.APPROVED,
    page: int = 1,
) -> Block:
    return Block(
        id=new_id(IdKind.BLOCK),
        ordinal=ordinal,
        block_type=BlockType.PARAGRAPH,
        text=text,
        provenance=Provenance(
            page_no=page,
            bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            extractor="digital-pdf",
            model_version="pypdfium2",
        ),
        confidence=0.9,
        review_state=state,
    )


def test_chunk_blocks_skips_rejected_and_orders() -> None:
    blocks = [
        _block(ordinal=1, text="second", page=2),
        _block(ordinal=0, text="first", page=1),
        _block(ordinal=2, text="gone", state=ReviewState.REJECTED),
    ]
    chunks = chunk_blocks(blocks, document_title="Spec")
    assert len(chunks) == 2
    assert [c.ordinal for c in chunks] == [0, 1]
    assert chunks[0].text_raw == "first"
    assert chunks[1].text_raw == "second"
    assert "Spec" in chunks[0].text_contextualized
    assert chunks[0].text_contextualized != chunks[0].text_raw
    assert chunks[0].page_numbers == [1]
    assert chunks[0].block_ids == [blocks[1].id]


def test_chunk_blocks_empty_when_all_rejected() -> None:
    blocks = [_block(ordinal=0, text="x", state=ReviewState.REJECTED)]
    assert chunk_blocks(blocks, document_title="Spec") == []
