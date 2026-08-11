"""TDD: vendored HybridChunker → sift Chunk mapping + Anthropic-style prefix."""

from __future__ import annotations

import statistics
from typing import Any

from sift_parse_core.transforms.chunker.tokenizer.base import BaseTokenizer
from sift_parse_core.types.doc import (
    BoundingBox,
    CoordOrigin,
    DoclingDocument,
    ProvenanceItem,
    Size,
)
from sift_parse_core.types.doc.labels import DocItemLabel

from sift_ingest.chunker import chunk_docling_document
from sift_ingest.contextual_prefix import PrefixCostRecord, PrefixGenerator


class _WordTokenizer(BaseTokenizer):  # type: ignore[misc]
    """Deterministic stand-in until BGE-M3 tokenizer lands in Phase 3."""

    def count_tokens(self, text: str) -> int:
        parts = text.split()
        return max(1, len(parts)) if parts else 1

    def get_max_tokens(self) -> int:
        return 512

    def get_tokenizer(self) -> Any:
        return lambda text: text.split()


class _FakePrefixLLM:
    """Injectable LLM: returns a known situating prefix + fixed USD cost."""

    def __init__(self, *, cost_usd: float = 0.008) -> None:
        self.cost_usd = cost_usd
        self.calls: list[tuple[str, str]] = []

    def generate(self, *, document_text: str, chunk_text: str) -> tuple[str, float]:
        self.calls.append((document_text, chunk_text))
        return (f"This chunk discusses: {chunk_text[:40].strip()}", self.cost_usd)


def _prov(page_no: int = 1) -> ProvenanceItem:
    return ProvenanceItem(
        page_no=page_no,
        bbox=BoundingBox(l=10, t=40, r=200, b=20, coord_origin=CoordOrigin.TOPLEFT),
        charspan=(0, 8),
    )


def _sample_doc(*, name: str = "sample") -> DoclingDocument:
    doc = DoclingDocument(name=name)
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    doc.add_heading(text="Overview", level=1, prov=_prov(1))
    doc.add_text(
        label=DocItemLabel.PARAGRAPH,
        text="Hybrid chunking keeps structure then respects token budgets.",
        prov=_prov(1),
    )
    doc.add_text(
        label=DocItemLabel.PARAGRAPH,
        text="Contextual prefixes situate each chunk inside the parent document.",
        prov=_prov(1),
    )
    return doc


def test_hybrid_chunker_emits_sift_chunks_with_section_path() -> None:
    doc = _sample_doc()
    chunks = chunk_docling_document(
        doc,
        document_title="Sample Spec",
        tokenizer=_WordTokenizer(),
    )
    assert len(chunks) > 0
    assert all(c.text_raw.strip() for c in chunks)
    assert all(isinstance(c.ordinal, int) and c.ordinal >= 0 for c in chunks)
    assert any(c.section_path for c in chunks)
    assert chunks[0].section_path[0] == "Overview"
    assert all(c.page_numbers for c in chunks)


def test_fake_llm_prefix_makes_contextualized_differ_from_raw() -> None:
    doc = _sample_doc()
    fake: PrefixGenerator = _FakePrefixLLM(cost_usd=0.009)
    cost_log: list[PrefixCostRecord] = []
    chunks = chunk_docling_document(
        doc,
        document_title="Sample Spec",
        tokenizer=_WordTokenizer(),
        prefix_generator=fake,
        document_text="Overview\n\nHybrid chunking...\n\nContextual prefixes...",
        cost_log=cost_log,
    )
    assert len(chunks) > 0
    assert fake.calls  # type: ignore[attr-defined]
    for chunk in chunks:
        assert chunk.text_contextualized != chunk.text_raw
        assert chunk.text_raw in chunk.text_contextualized
        assert chunk.text_contextualized.startswith("This chunk discusses:")
    assert cost_log
    assert cost_log[0].total_usd > 0
    assert cost_log[0].chunk_count == len(chunks)


def test_prefix_cost_median_under_five_cents_on_synthetic_golden() -> None:
    fake = _FakePrefixLLM(cost_usd=0.008)
    per_doc: list[float] = []
    for i in range(5):
        cost_log: list[PrefixCostRecord] = []
        chunks = chunk_docling_document(
            _sample_doc(name=f"golden-{i}"),
            document_title=f"Doc {i}",
            tokenizer=_WordTokenizer(),
            prefix_generator=fake,
            document_text=f"document body {i}",
            cost_log=cost_log,
        )
        assert len(chunks) > 0
        assert cost_log
        per_doc.append(cost_log[0].total_usd)
    assert statistics.median(per_doc) < 0.05
