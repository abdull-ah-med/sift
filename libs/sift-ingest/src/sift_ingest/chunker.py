"""Chunking for Phase 2: HybridChunker + optional Anthropic contextual prefix.

``chunk_blocks`` remains the block-list finalize path until DoclingDocument
persistence is wired. ``chunk_docling_document`` is the Phase 2 §3 contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sift_parse_core.transforms.chunker.hybrid_chunker import HybridChunker
from sift_parse_core.transforms.chunker.tokenizer.base import BaseTokenizer
from sift_parse_core.types.doc import DoclingDocument
from sift_parse_core.types.doc.document import CodeItem, SectionHeaderItem, TableItem, TitleItem

from sift_core.chunk import Chunk, ChunkType
from sift_core.ids import IdKind, new_id
from sift_core.models import Block, BlockType, ReviewState
from sift_ingest.contextual_prefix import (
    PrefixCostRecord,
    PrefixGenerator,
    apply_contextual_prefixes,
)

if TYPE_CHECKING:
    from sift_parse_core.transforms.chunker.doc_chunk import DocChunk

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


class _WordTokenizer(BaseTokenizer):  # type: ignore[misc]
    """Deterministic stand-in until the BGE-M3 tokenizer is wired in Phase 3."""

    def count_tokens(self, text: str) -> int:
        parts = text.split()
        return max(1, len(parts)) if parts else 1

    def get_max_tokens(self) -> int:
        return 512

    def get_tokenizer(self) -> Any:
        return lambda text: text.split()


def _approx_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _contextualize(*, document_title: str, block: Block, text: str) -> str:
    page = block.provenance.page_no
    return f"From document '{document_title}', page {page}:\n\n{text}"


def _page_numbers(doc_chunk: DocChunk) -> list[int]:
    pages: list[int] = []
    seen: set[int] = set()
    for item in doc_chunk.meta.doc_items:
        for prov in item.prov or []:
            page = int(prov.page_no)
            if page not in seen:
                seen.add(page)
                pages.append(page)
    return pages or [1]


def _chunk_type(doc_chunk: DocChunk) -> ChunkType:
    for item in doc_chunk.meta.doc_items:
        if isinstance(item, TableItem):
            return ChunkType.TABLE
        if isinstance(item, CodeItem):
            return ChunkType.CODE
    return ChunkType.PROSE


def _block_ids(doc_chunk: DocChunk, block_id_by_ref: dict[str, str] | None) -> list[str]:
    if not block_id_by_ref:
        return []
    out: list[str] = []
    for item in doc_chunk.meta.doc_items:
        if isinstance(item, TitleItem | SectionHeaderItem):
            continue
        ref = getattr(item, "self_ref", None)
        if isinstance(ref, str) and ref in block_id_by_ref:
            out.append(block_id_by_ref[ref])
    return out


def chunk_docling_document(
    doc: DoclingDocument,
    *,
    document_title: str,
    tokenizer: BaseTokenizer | None = None,
    prefix_generator: PrefixGenerator | None = None,
    document_text: str | None = None,
    cost_log: list[PrefixCostRecord] | None = None,
    block_id_by_ref: dict[str, str] | None = None,
) -> list[Chunk]:
    """Run vendored ``HybridChunker`` then optional contextual prefix."""
    del document_title  # reserved for future non-LLM fallback prefix
    chunker = HybridChunker(tokenizer=tokenizer or _WordTokenizer())
    mapped: list[Chunk] = []
    for ordinal, doc_chunk in enumerate(chunker.chunk(dl_doc=doc)):
        text = (doc_chunk.text or "").strip()
        if not text:
            continue
        headings = list(doc_chunk.meta.headings or [])
        mapped.append(
            Chunk(
                id=new_id(IdKind.CHUNK),
                ordinal=ordinal,
                text_raw=text,
                text_contextualized=text,
                token_count=_approx_tokens(text),
                chunk_type=_chunk_type(doc_chunk),
                section_path=headings,
                page_numbers=_page_numbers(doc_chunk),
                block_ids=_block_ids(doc_chunk, block_id_by_ref),
                quality_score=None,
            )
        )
    # Re-number after skipping empties.
    mapped = [c.model_copy(update={"ordinal": i}) for i, c in enumerate(mapped)]

    if prefix_generator is None:
        return mapped

    return apply_contextual_prefixes(
        mapped,
        document_text=document_text or "",
        generator=prefix_generator,
        cost_log=cost_log,
    )


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
