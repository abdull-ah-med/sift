"""Equation heuristic absorption smoke tests."""

from __future__ import annotations

from sift_core.models import Block, BlockType, BoundingBox, Provenance
from sift_ingest.equation_flags import flag_equation_blocks


def _block(
    text: str,
    *,
    ordinal: int = 0,
    block_kind: BlockType = BlockType.PARAGRAPH,
) -> Block:
    return Block(
        id=f"blk_{ordinal}",
        ordinal=ordinal,
        block_type=block_kind,
        text=text,
        provenance=Provenance(
            page_no=1,
            bbox=BoundingBox(x0=0, y0=0, x1=1, y1=1),
            extractor="test",
            model_version="0",
        ),
    )


def test_flag_equation_blocks_retags_math_paragraph() -> None:
    theta = "\u03b8"
    sigma = "\u2211"
    alpha = "\u03b1"
    math = f"L({theta}) = {sigma}_i x_i + {alpha}"
    blocks = [
        _block("The loss is defined as", ordinal=0),
        _block(math, ordinal=1),
    ]
    out = flag_equation_blocks(blocks)
    assert out[1].block_type == BlockType.FORMULA
    assert out[0].block_type == BlockType.PARAGRAPH
