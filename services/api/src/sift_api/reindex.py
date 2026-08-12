"""Reindex collection embeddings into Qdrant (Phase 3 §4)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from sift_api.audit_emit import emit_audit
from sift_api.db import sync_dsn
from sift_api.settings import Settings, get_settings
from sift_core.db import tenant_guc_statements
from sift_retrieve.store.qdrant import QdrantDenseStore

AuditFn = Callable[..., None]


def _collection_exists(conn: Any, *, collection_id: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM collections WHERE id = :id AND deleted_at IS NULL"),
        {"id": collection_id},
    ).first()
    return row is not None


def run_reindex_to_qdrant(
    *,
    collection_id: str,
    tenant_id: str,
    actor: str,
    engine: Engine | None = None,
    settings: Settings | None = None,
    qdrant: QdrantDenseStore | None = None,
    audit: AuditFn | None = None,
) -> dict[str, Any]:
    """Copy dense embeddings for a collection into Qdrant and set vector_backend."""
    cfg = settings or get_settings()
    audit_fn = audit or emit_audit
    store = qdrant or QdrantDenseStore(base_url=cfg.sift_qdrant_url)
    own_engine = engine is None
    eng = engine or create_engine(sync_dsn(cfg))
    try:
        with eng.begin() as conn:
            conn.execute(text("SET LOCAL ROLE sift_app"))
            for stmt in tenant_guc_statements(tenant_id):
                conn.execute(text(stmt))
            if not _collection_exists(conn, collection_id=collection_id):
                msg = "collection not found"
                raise LookupError(msg)
            rows = (
                conn.execute(
                    text(
                        """
                        SELECT e.chunk_id, c.document_id, e.embedding
                        FROM chunk_embeddings e
                        JOIN chunks c ON c.id = e.chunk_id
                        WHERE e.tenant_id = :tid
                          AND e.collection_id = :cid
                          AND c.review_state IN ('approved', 'edited')
                        """
                    ),
                    {"tid": tenant_id, "cid": collection_id},
                )
                .mappings()
                .all()
            )
        points: list[dict[str, Any]] = []
        for r in rows:
            emb = r["embedding"]
            if hasattr(emb, "tolist"):
                emb = emb.tolist()
            elif isinstance(emb, str):
                emb = [float(x) for x in emb.strip("[]").split(",") if x.strip()]
            else:
                emb = [float(x) for x in emb]
            points.append(
                {
                    "id": r["chunk_id"],
                    "vector": emb,
                    "payload": {
                        "chunk_id": r["chunk_id"],
                        "document_id": r["document_id"],
                        "tenant_id": tenant_id,
                        "collection_id": collection_id,
                    },
                }
            )
        store.ensure_collection(tenant_id=tenant_id, collection_id=collection_id, dim=1024)
        if points:
            # Batch upsert in chunks of 64
            for i in range(0, len(points), 64):
                store.upsert_points(
                    tenant_id=tenant_id,
                    collection_id=collection_id,
                    points=points[i : i + 64],
                )
        with eng.begin() as conn:
            conn.execute(text("SET LOCAL ROLE sift_app"))
            for stmt in tenant_guc_statements(tenant_id):
                conn.execute(text(stmt))
            conn.execute(
                text(
                    """
                    UPDATE collections
                    SET vector_backend = 'qdrant',
                        qdrant_collection = :qname
                    WHERE id = :id
                    """
                ),
                {
                    "id": collection_id,
                    "qname": f"{tenant_id}__{collection_id}",
                },
            )
    finally:
        if own_engine:
            eng.dispose()

    audit_fn(
        tenant_id=tenant_id,
        actor=actor,
        action="collection.reindex",
        target_kind="collection",
        target_id=collection_id,
        payload={"backend": "qdrant", "points": len(points)},
    )
    return {"backend": "qdrant", "points": len(points)}
