"""Chunking for Phase 2: HybridChunker + optional Anthropic contextual prefix.

``chunk_blocks`` remains the block-list finalize path until DoclingDocument
persistence is wired. ``chunk_docling_document`` is the Phase 2 §3 contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sift_core.chunk import Chunk, ChunkType
from sift_core.ids import IdKind, new_id
from sift_core.models import Block, BlockType, ReviewState

from sift_ingest.contextual_prefix import PrefixCostRecord, PrefixGenerator

if TYPE_CHECKING:
    from sift_parse_core.transforms.chunker.tokenizer.base import BaseTokenizer
    from sift_parse_core.types.doc import DoclingDocument

_REJECTED = frozenset({ReviewState.REJECTED})

_TYPE_MAP: dict[BlockType, ChunkType] = {
    BlockType.PARAGRAPH: ChunkType.PROSE,
    BlockType.HEADING: ChunkType.PROSE,
    BlockType.LIST_ITEM: ChunkType.PROSE,
    BlockType.CAPTION: ChunkType.FIGURE_CAPTION,
    BlockType.FOOTNOTE: ChunkType.PROSE,
    BlockType.TABLE: ChunkType.TABLE,
    BlockType.FIGURE: ChunkType.FIGURE_CAPTION,
    BlockType.FORMULA: ChunkType.FORMULA,
    BlockType.CODE: ChunkType.CODE,
}


def _approx_tokens(text: str) -> int:
    # Cheap stand-in until the BGE-M3 tokenizer is wired in Phase 3.
    return max(1, len(text.split()))


def _contextualize(*, document_title: str, block: Block, text: str) -> str:
    page = block.provenance.page_no
    return f"From document '{document_title}', page {page}:\n\n{text}"


def chunk_docling_document(
    doc: DoclingDocument,
    *,
    document_title: str,
    tokenizer: BaseTokenizer | None = None,
    prefix_generator: PrefixGenerator | None = None,
    document_text: str | None = None,
    cost_log: list[PrefixCostRecord] | None = None,
) -> list[Chunk]:
    """Run vendored ``HybridChunker`` then optional contextual prefix.

    TDD stub — returns empty until the impl commit.
    """
    del doc, document_title, tokenizer, prefix_generator, document_text, cost_log
    return []


def chunk_blocks(
    blocks: list[Block],
    *,
    document_title: str,
) -> list[Chunk]:
    """Map reviewable blocks to ordered chunks (skips rejected)."""
    chunks: list[Chunk] = []
    ordinal = 0
    for block in sorted(blocks, key=lambda b: b.ordinal):
        if block.review_state in _REJECTED:
            continue
        text = (block.text or "").strip()
        if not text:
            continue
        contextualized = _contextualize(document_title=document_title, block=block, text=text)
        chunks.append(
            Chunk(
                id=new_id(IdKind.CHUNK),
                ordinal=ordinal,
                text_raw=text,
                text_contextualized=contextualized,
                token_count=_approx_tokens(contextualized),
                chunk_type=_TYPE_MAP.get(block.block_type, ChunkType.PROSE),
                section_path=list(block.hierarchy or []),
                page_numbers=[block.provenance.page_no],
                block_ids=[block.id],
                quality_score=block.confidence,
            )
        )
        ordinal += 1
    return chunks
