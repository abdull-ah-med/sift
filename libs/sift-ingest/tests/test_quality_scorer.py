"""Quality scorer absorption smoke tests."""

from __future__ import annotations

from sift_core.chunk import Chunk, ChunkType
from sift_core.models import Block, BlockType, BoundingBox, Provenance
from sift_ingest.quality_scorer import score_chunks


def test_score_chunks_sets_quality_score() -> None:
    block = Block(
        id="blk_1",
        ordinal=0,
        block_type=BlockType.PARAGRAPH,
        text="Hello world. This is a clean sentence.",
        confidence=0.9,
        provenance=Provenance(
            page_no=1,
            bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            extractor="test",
            model_version="0",
        ),
    )
    chunk = Chunk(
        id="chk_1",
        ordinal=0,
        text_raw=block.text or "",
        text_contextualized=block.text or "",
        token_count=8,
        chunk_type=ChunkType.PROSE,
        block_ids=["blk_1"],
    )
    scored = score_chunks([chunk], [block])
    assert scored[0].quality_score is not None
    assert 0.0 <= scored[0].quality_score <= 1.0
