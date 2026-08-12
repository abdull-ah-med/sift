"""Automatable Phase 2 §10 exit-gate evidence (p2re-7)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "evals" / "corpus"


def test_vendor_sift_ingest_deleted() -> None:
    assert not (ROOT / "vendor" / "sift-ingest").exists()


def test_golden_digital_corpus_parses_with_provenance() -> None:
    from sift.parse import DigitalPdfParser, ParseConfig

    pdfs = sorted(CORPUS.glob("digital-*.pdf"))
    assert len(pdfs) >= 5
    parser = DigitalPdfParser()
    cfg = ParseConfig()
    for pdf in pdfs:
        result = parser.parse(pdf, cfg)
        assert result.blocks, f"{pdf.name}: expected blocks"
        for block in result.blocks:
            assert block.provenance.page_no >= 1
            assert block.provenance.bbox is not None
            assert block.provenance.extractor
            assert block.provenance.model_version is not None


def test_chunk_path_yields_contextualized_chunks() -> None:
    from sift.parse import DigitalPdfParser, ParseConfig
    from sift_ingest.chunker import chunk_blocks

    pdf = CORPUS / "digital-02-with-heading.pdf"
    result = DigitalPdfParser().parse(pdf, ParseConfig())
    chunks = chunk_blocks(result.blocks, document_title="Exit Gate Doc")
    assert len(chunks) > 0
    assert any(c.text_contextualized != c.text_raw for c in chunks)


def test_time_to_first_chunk_proxy_under_45s() -> None:
    """Parse + chunk a multi-page digital PDF; budget from Phase 2 §10."""
    from sift.parse import DigitalPdfParser, ParseConfig
    from sift_ingest.chunker import chunk_blocks

    pdf = CORPUS / "pdf" / "prompt_injection_liu_2023.pdf"
    if not pdf.is_file():
        pytest.skip("multi-page corpus PDF missing")
    t0 = time.perf_counter()
    result = DigitalPdfParser().parse(pdf, ParseConfig())
    chunks = chunk_blocks(result.blocks, document_title="TTF probe")
    elapsed = time.perf_counter() - t0
    assert len(chunks) > 0
    assert elapsed < 45.0, f"time-to-first-chunk proxy {elapsed:.3f}s exceeds 45s"


def test_prefix_cost_record_under_budget() -> None:
    from sift_core.chunk import Chunk, ChunkType
    from sift_ingest.contextual_prefix import PrefixCostRecord, apply_contextual_prefixes

    class _Cheap:
        def generate(self, *, document_text: str, chunk_text: str) -> tuple[str, float]:
            del document_text, chunk_text
            return "This chunk discusses: exit gates.", 0.001

    chunks = [
        Chunk(
            id="chk_1",
            ordinal=0,
            text_raw="Hello world",
            text_contextualized="Hello world",
            token_count=2,
            chunk_type=ChunkType.PROSE,
        )
    ]
    cost_log: list[PrefixCostRecord] = []
    out = apply_contextual_prefixes(
        chunks,
        document_text="doc",
        generator=_Cheap(),
        cost_log=cost_log,
    )
    assert out[0].text_contextualized != out[0].text_raw
    assert cost_log and cost_log[0].total_usd < 0.05
