"""Hybrid dense + BM25 → RRF → optional rerank."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from sift_retrieve.rrf import RRF_K, rrf_fuse_scored

CANDIDATE_LIMIT = 50


@dataclass(frozen=True)
class RetrieveHit:
    chunk_id: str
    document_id: str
    score: float
    rerank_score: float | None = None
    text: str | None = None


class _DenseSearcher(Protocol):
    def search(
        self,
        *,
        query_vector: Sequence[float],
        tenant_id: str,
        collection_id: str,
        limit: int = 50,
        document_ids: Sequence[str] | None = None,
    ) -> list[RetrieveHit]: ...


class _Bm25Searcher(Protocol):
    def search(
        self,
        *,
        query: str,
        tenant_id: str,
        collection_id: str,
        limit: int = 50,
        document_ids: Sequence[str] | None = None,
    ) -> list[RetrieveHit]: ...


class _Embedder(Protocol):
    def embed(self, texts: list[str], *, batch_size: int = 64) -> list[list[float]]: ...


class _Reranker(Protocol):
    def rerank(
        self,
        *,
        query: str,
        documents: list[tuple[str, str]],
    ) -> list[tuple[str, float]]: ...


class HybridRetriever:
    """Dense + BM25 hybrid with RRF (k=60) and optional TEI rerank."""

    def __init__(
        self,
        *,
        dense: _DenseSearcher,
        bm25: _Bm25Searcher,
        tei: _Embedder,
        reranker: _Reranker | None = None,
        load_texts: Callable[[list[str]], dict[str, str]] | None = None,
    ) -> None:
        self._dense = dense
        self._bm25 = bm25
        self._tei = tei
        self._reranker = reranker
        self._load_texts = load_texts or (lambda _ids: {})

    def retrieve(  # noqa: PLR0913 — retrieve filter surface
        self,
        *,
        query: str,
        tenant_id: str,
        collection_id: str,
        top_k: int = 10,
        rerank: bool = True,
        document_ids: Sequence[str] | None = None,
    ) -> list[RetrieveHit]:
        if document_ids is not None and len(document_ids) == 0:
            return []

        candidate_limit = max(CANDIDATE_LIMIT, top_k)
        vectors = self._tei.embed([query])
        if not vectors:
            return []
        q_dense = vectors[0]
        dense_hits = self._dense.search(
            query_vector=q_dense,
            tenant_id=tenant_id,
            collection_id=collection_id,
            limit=candidate_limit,
            document_ids=document_ids,
        )
        bm25_hits = self._bm25.search(
            query=query,
            tenant_id=tenant_id,
            collection_id=collection_id,
            limit=candidate_limit,
            document_ids=document_ids,
        )
        by_id: dict[str, RetrieveHit] = {}
        for hit in dense_hits + bm25_hits:
            prev = by_id.get(hit.chunk_id)
            if prev is None or hit.score > prev.score:
                by_id[hit.chunk_id] = hit

        fused_scored = rrf_fuse_scored(
            [
                [h.chunk_id for h in dense_hits],
                [h.chunk_id for h in bm25_hits],
            ],
            k=RRF_K,
            limit=candidate_limit,
        )
        fused = [
            RetrieveHit(
                chunk_id=cid,
                document_id=by_id[cid].document_id,
                score=rrf_score,
                text=by_id[cid].text,
            )
            for cid, rrf_score in fused_scored
            if cid in by_id
        ]

        if not rerank or self._reranker is None or not fused:
            return fused[:top_k]

        texts = self._load_texts([h.chunk_id for h in fused])
        docs = [(h.chunk_id, texts.get(h.chunk_id, "")) for h in fused]
        # Avoid TEI ranking empty passages when the caller did not supply texts.
        if not any(text for _cid, text in docs):
            return fused[:top_k]

        ranked = self._reranker.rerank(query=query, documents=docs)
        score_map = dict(ranked)
        out: list[RetrieveHit] = []
        for cid, rscore in ranked[:top_k]:
            base = by_id[cid]
            out.append(
                RetrieveHit(
                    chunk_id=base.chunk_id,
                    document_id=base.document_id,
                    score=base.score,
                    rerank_score=rscore,
                    text=texts.get(cid),
                )
            )
        # Keep stable fill if reranker dropped ids
        if len(out) < top_k:
            seen = {h.chunk_id for h in out}
            for hit in fused:
                if hit.chunk_id in seen:
                    continue
                out.append(
                    RetrieveHit(
                        chunk_id=hit.chunk_id,
                        document_id=hit.document_id,
                        score=hit.score,
                        rerank_score=score_map.get(hit.chunk_id),
                        text=texts.get(hit.chunk_id),
                    )
                )
                if len(out) >= top_k:
                    break
        return out
