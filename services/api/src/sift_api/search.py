"""Collection hybrid search orchestration (Phase 3 §3.3)."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import Engine

from sift_api.audit_emit import emit_audit
from sift_api.db import sync_dsn
from sift_api.schemas import SearchHitOut, SearchResponse
from sift_api.settings import Settings, get_settings
from sift_api.tei import TeiClient
from sift_core.db import tenant_guc_statements
from sift_retrieve.hybrid import RetrieveHit
from sift_retrieve.rerank import TeiReranker
from sift_retrieve.rrf import RRF_K, rrf_fuse_scored
from sift_retrieve.store.bm25 import ParadeBm25Store
from sift_retrieve.store.pgvector import PgvectorDenseStore
from sift_retrieve.store.qdrant import QdrantDenseStore

AuditFn = Callable[..., None]
CANDIDATE_LIMIT = 50


def query_hash(query: str) -> str:
    """SHA-256 hex digest of the raw query (audit privacy; never store raw)."""
    return hashlib.sha256(query.encode("utf-8"), usedforsecurity=False).hexdigest()


def _with_tenant(conn: Connection, tenant_id: str) -> None:
    conn.execute(text("SET LOCAL ROLE sift_app"))
    for stmt in tenant_guc_statements(tenant_id):
        conn.execute(text(stmt))


def _collection_exists(conn: Connection, *, collection_id: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM collections WHERE id = :id AND deleted_at IS NULL"),
        {"id": collection_id},
    ).first()
    return row is not None


def _resolve_document_ids(
    conn: Connection,
    *,
    collection_id: str,
    document_ids: Sequence[str] | None,
    tags: Sequence[str] | None,
) -> list[str] | None:
    """Intersect explicit document_ids with tag filter; None = unrestricted."""
    if not tags and document_ids is None:
        return None
    if document_ids is not None and len(document_ids) == 0:
        return []
    if tags and not document_ids:
        rows = conn.execute(
            text(
                """
                SELECT id FROM documents
                WHERE collection_id = :cid
                  AND deleted_at IS NULL
                  AND tags @> :tags
                """
            ),
            {"cid": collection_id, "tags": list(tags)},
        ).fetchall()
        return [str(r[0]) for r in rows]
    if tags and document_ids is not None:
        rows = conn.execute(
            text(
                """
                SELECT id FROM documents
                WHERE collection_id = :cid
                  AND deleted_at IS NULL
                  AND id = ANY(:ids)
                  AND tags @> :tags
                """
            ),
            {"cid": collection_id, "ids": list(document_ids), "tags": list(tags)},
        ).fetchall()
        return [str(r[0]) for r in rows]
    return list(document_ids) if document_ids is not None else None


def _load_hit_meta(conn: Connection, chunk_ids: list[str]) -> dict[str, dict[str, Any]]:
    if not chunk_ids:
        return {}
    rows = conn.execute(
        text(
            """
            SELECT c.id AS chunk_id, c.text_contextualized AS text,
                   c.section_path, c.page_numbers, c.block_ids,
                   d.title AS document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.id = ANY(:ids)
            """
        ),
        {"ids": chunk_ids},
    ).mappings()
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        out[str(r["chunk_id"])] = {
            "text": r["text"],
            "section_path": list(r["section_path"] or []),
            "page_numbers": list(r["page_numbers"] or []),
            "block_ids": list(r["block_ids"] or []),
            "document_title": r["document_title"],
        }
    return out


def _store_search(
    conn: Connection,
    *,
    query: str,
    query_vector: Sequence[float],
    tenant_id: str,
    collection_id: str,
    top_k: int,
    document_ids: Sequence[str] | None,
    dense_hits: list[RetrieveHit] | None = None,
) -> tuple[list[RetrieveHit], dict[str, dict[str, Any]]]:
    """Dense + BM25 + RRF inside an open tenant transaction (no TEI calls).

    When ``dense_hits`` is provided (Qdrant path), skip pgvector and fuse with BM25 only.
    """
    candidate_limit = max(CANDIDATE_LIMIT, top_k)
    if dense_hits is None:
        dense_hits = PgvectorDenseStore(conn).search(
            query_vector=query_vector,
            tenant_id=tenant_id,
            collection_id=collection_id,
            limit=candidate_limit,
            document_ids=document_ids,
        )
    bm25_hits = ParadeBm25Store(conn).search(
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
        )
        for cid, rrf_score in fused_scored
        if cid in by_id
    ]
    meta = _load_hit_meta(conn, [h.chunk_id for h in fused])
    return fused, meta


def _collection_vector_backend(conn: Connection, *, collection_id: str) -> str:
    row = conn.execute(
        text(
            """
            SELECT coalesce(vector_backend, 'pgvector') AS vector_backend
            FROM collections
            WHERE id = :id AND deleted_at IS NULL
            """
        ),
        {"id": collection_id},
    ).mappings().one_or_none()
    if row is None:
        return "pgvector"
    return str(row["vector_backend"] or "pgvector")


def _hybrid_retrieve(
    *,
    query: str,
    tenant_id: str,
    collection_id: str,
    top_k: int,
    document_ids: Sequence[str] | None,
    rerank: bool,
    settings: Settings,
    engine: Engine,
) -> tuple[list[RetrieveHit], dict[str, dict[str, Any]]]:
    """Embed/rerank outside DB; dense+BM25 inside short transactions."""
    tei = TeiClient(base_url=settings.sift_tei_url, model=settings.sift_tei_model)
    vectors = tei.embed([query])
    if not vectors:
        return [], {}
    q_dense = vectors[0]

    with engine.begin() as conn:
        _with_tenant(conn, tenant_id)
        backend = _collection_vector_backend(conn, collection_id=collection_id)
        if backend == "qdrant" or settings.sift_vector_backend == "qdrant":
            backend = "qdrant"

    dense_hits: list[RetrieveHit] | None = None
    if backend == "qdrant":
        candidate_limit = max(CANDIDATE_LIMIT, top_k)
        dense_hits = QdrantDenseStore(
            base_url=settings.sift_qdrant_url,
            api_key=settings.sift_qdrant_api_key or None,
        ).search(
            query_vector=q_dense,
            tenant_id=tenant_id,
            collection_id=collection_id,
            limit=candidate_limit,
            document_ids=document_ids,
        )

    with engine.begin() as conn:
        _with_tenant(conn, tenant_id)
        fused, meta = _store_search(
            conn,
            query=query,
            query_vector=q_dense,
            tenant_id=tenant_id,
            collection_id=collection_id,
            top_k=top_k,
            document_ids=document_ids,
            dense_hits=dense_hits,
        )

    if not rerank or not fused:
        return fused[:top_k], meta

    docs = [(h.chunk_id, str(meta.get(h.chunk_id, {}).get("text") or "")) for h in fused]
    if not any(text for _cid, text in docs):
        return fused[:top_k], meta

    reranker = TeiReranker(base_url=settings.sift_tei_rerank_url)
    ranked = reranker.rerank(query=query, documents=docs)
    by_id = {h.chunk_id: h for h in fused}
    out: list[RetrieveHit] = []
    for cid, rscore in ranked[:top_k]:
        base = by_id[cid]
        out.append(
            RetrieveHit(
                chunk_id=base.chunk_id,
                document_id=base.document_id,
                score=base.score,
                rerank_score=rscore,
                text=str(meta.get(cid, {}).get("text") or "") or None,
            )
        )
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
                    text=str(meta.get(hit.chunk_id, {}).get("text") or "") or None,
                )
            )
            if len(out) >= top_k:
                break
    return out, meta


def run_collection_search(
    *,
    collection_id: str,
    tenant_id: str,
    actor: str,
    query: str,
    top_k: int = 10,
    document_ids: Sequence[str] | None = None,
    tags: Sequence[str] | None = None,
    include_text: bool = True,
    include_provenance: bool = True,
    rerank: bool = True,
    engine: Engine | None = None,
    settings: Settings | None = None,
    audit: AuditFn | None = None,
) -> SearchResponse:
    """Run hybrid search under tenant RLS; audit ``search.query`` with query_hash only."""
    cfg = settings or get_settings()
    audit_fn = audit or emit_audit
    own_engine = engine is None
    eng = engine or create_engine(sync_dsn(cfg))
    try:
        with eng.begin() as conn:
            _with_tenant(conn, tenant_id)
            if not _collection_exists(conn, collection_id=collection_id):
                msg = "collection not found"
                raise LookupError(msg)
            resolved_ids = _resolve_document_ids(
                conn,
                collection_id=collection_id,
                document_ids=document_ids,
                tags=tags,
            )

        hits, meta = _hybrid_retrieve(
            query=query,
            tenant_id=tenant_id,
            collection_id=collection_id,
            top_k=top_k,
            document_ids=resolved_ids,
            rerank=rerank,
            settings=cfg,
            engine=eng,
        )
    finally:
        if own_engine:
            eng.dispose()

    results: list[SearchHitOut] = []
    for hit in hits:
        m = meta.get(hit.chunk_id, {})
        results.append(
            SearchHitOut(
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                document_title=m.get("document_title"),
                score=float(hit.score),
                rerank_score=hit.rerank_score,
                text=(m.get("text") if include_text else None),
                section_path=(m.get("section_path") if include_provenance else None),
                page_numbers=(m.get("page_numbers") if include_provenance else None),
                block_ids=(m.get("block_ids") if include_provenance else None),
            )
        )

    qh = query_hash(query)
    audit_fn(
        tenant_id=tenant_id,
        actor=actor,
        action="search.query",
        target_kind="collection",
        target_id=collection_id,
        payload={
            "query_hash": qh,
            "top_k": top_k,
            "result_count": len(results),
            "rerank": rerank,
        },
    )
    return SearchResponse(results=results, trace_id=str(uuid.uuid4()))
