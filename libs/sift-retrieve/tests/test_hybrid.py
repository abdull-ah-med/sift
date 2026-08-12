"""Hybrid retrieve contracts (p3-4 / Phase 3 §3.1)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from sift_retrieve.hybrid import HybridRetriever, RetrieveHit
from sift_retrieve.rrf import RRF_K


def test_rrf_k_is_sixty() -> None:
    assert RRF_K == 60


def test_hybrid_retrieve_dense_bm25_rrf_then_rerank() -> None:
    dense = MagicMock()
    dense.search.return_value = [
        RetrieveHit(chunk_id="c1", document_id="d1", score=0.9),
        RetrieveHit(chunk_id="c2", document_id="d1", score=0.8),
        RetrieveHit(chunk_id="c3", document_id="d2", score=0.7),
    ]
    bm25 = MagicMock()
    bm25.search.return_value = [
        RetrieveHit(chunk_id="c2", document_id="d1", score=12.0),
        RetrieveHit(chunk_id="c4", document_id="d3", score=10.0),
        RetrieveHit(chunk_id="c1", document_id="d1", score=8.0),
    ]
    tei = MagicMock()
    tei.embed.return_value = [[0.1] * 1024]
    reranker = MagicMock()
    reranker.rerank.return_value = [
        ("c2", 0.99),
        ("c1", 0.88),
        ("c4", 0.70),
    ]

    def load_texts(chunk_ids: list[str]) -> dict[str, str]:
        return {cid: f"text-{cid}" for cid in chunk_ids}

    retriever = HybridRetriever(
        dense=dense,
        bm25=bm25,
        tei=tei,
        reranker=reranker,
        load_texts=load_texts,
    )
    hits = retriever.retrieve(
        query="refund policy",
        tenant_id="ten_1",
        collection_id="col_1",
        top_k=2,
        rerank=True,
    )

    tei.embed.assert_called_once_with(["refund policy"])
    dense.search.assert_called_once()
    bm25.search.assert_called_once()
    assert bm25.search.call_args.kwargs["query"] == "refund policy"
    assert dense.search.call_args.kwargs["tenant_id"] == "ten_1"
    assert dense.search.call_args.kwargs["collection_id"] == "col_1"
    reranker.rerank.assert_called_once()
    assert [h.chunk_id for h in hits] == ["c2", "c1"]
    assert hits[0].rerank_score == 0.99


def test_hybrid_retrieve_skips_rerank_when_disabled() -> None:
    dense = MagicMock()
    dense.search.return_value = [
        RetrieveHit(chunk_id="a", document_id="d", score=0.5),
    ]
    bm25 = MagicMock()
    bm25.search.return_value = [
        RetrieveHit(chunk_id="a", document_id="d", score=1.0),
    ]
    tei = MagicMock()
    tei.embed.return_value = [[0.0] * 1024]
    reranker = MagicMock()

    retriever = HybridRetriever(
        dense=dense,
        bm25=bm25,
        tei=tei,
        reranker=reranker,
        load_texts=lambda ids: {i: i for i in ids},
    )
    hits = retriever.retrieve(
        query="q",
        tenant_id="t",
        collection_id="c",
        top_k=10,
        rerank=False,
    )
    reranker.rerank.assert_not_called()
    assert hits[0].chunk_id == "a"
    assert hits[0].rerank_score is None


def test_hybrid_retrieve_never_logs_raw_query(capsys: Any) -> None:
    dense = MagicMock()
    dense.search.return_value = []
    bm25 = MagicMock()
    bm25.search.return_value = []
    tei = MagicMock()
    tei.embed.return_value = [[0.0] * 1024]

    HybridRetriever(
        dense=dense,
        bm25=bm25,
        tei=tei,
        reranker=MagicMock(),
        load_texts=lambda _ids: {},
    ).retrieve(
        query="SECRET_QUERY_SHOULD_NOT_PRINT",
        tenant_id="t",
        collection_id="c",
        top_k=5,
        rerank=False,
    )
    captured = capsys.readouterr()
    assert "SECRET_QUERY_SHOULD_NOT_PRINT" not in captured.out
    assert "SECRET_QUERY_SHOULD_NOT_PRINT" not in captured.err
