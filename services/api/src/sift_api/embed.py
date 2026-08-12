"""embed_document orchestration: approved chunks → TEI dense → pgvector (ADR-0021)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from sift_api.db import sync_dsn
from sift_api.settings import Settings, get_settings
from sift_api.tei import TeiClient
from sift_core.audit import write_audit_event

EMBED_BATCH = 64
EMBED_DIM = 1024
EMBED_MODEL_LABEL = "bge-m3"

LoadChunksFn = Callable[..., list[dict[str, Any]]]
UpsertFn = Callable[..., None]
MarkReadyFn = Callable[..., None]
BumpIndexFn = Callable[..., None]
AuditFn = Callable[..., None]


def load_chunks_needing_embed(
    conn: Connection,
    *,
    document_id: str,
    tenant_id: str,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Return approved/edited chunks missing embeddings (or all if ``force``)."""
    if force:
        sql = """
            SELECT c.id, c.collection_id, c.text_contextualized, c.review_state
            FROM chunks c
            WHERE c.document_id = :document_id
              AND c.tenant_id = :tenant_id
              AND c.review_state IN ('approved', 'edited')
            ORDER BY c.ordinal
            """
    else:
        sql = """
            SELECT c.id, c.collection_id, c.text_contextualized, c.review_state
            FROM chunks c
            LEFT JOIN chunk_embeddings e ON e.chunk_id = c.id
            WHERE c.document_id = :document_id
              AND c.tenant_id = :tenant_id
              AND c.review_state IN ('approved', 'edited')
              AND e.chunk_id IS NULL
            ORDER BY c.ordinal
            """
    rows = conn.execute(
        text(sql),
        {"document_id": document_id, "tenant_id": tenant_id},
    ).mappings()
    return [dict(r) for r in rows]


def upsert_chunk_embeddings(  # noqa: PLR0913 — upsert columns are the public contract
    conn: Connection,
    *,
    tenant_id: str,
    collection_id: str,
    chunk_ids: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    sparse: None = None,
    model: str = EMBED_MODEL_LABEL,
    dim: int = EMBED_DIM,
) -> None:
    """Upsert dense vectors; ``sparse`` is always NULL under ADR-0021."""
    if sparse is not None:
        msg = "sparse embeddings are disabled until TEI BGE-M3 sparse ships (ADR-0021)"
        raise ValueError(msg)
    for chunk_id, vector in zip(chunk_ids, embeddings, strict=True):
        if len(vector) != dim:
            msg = f"expected {dim}-d embedding, got {len(vector)}"
            raise ValueError(msg)
        vec_literal = "[" + ",".join(str(float(x)) for x in vector) + "]"
        conn.execute(
            text(
                """
                INSERT INTO chunk_embeddings (
                  chunk_id, tenant_id, collection_id, model, dim, embedding, sparse
                ) VALUES (
                  :chunk_id, :tenant_id, :collection_id, :model, :dim,
                  CAST(:embedding AS vector), NULL
                )
                ON CONFLICT (chunk_id) DO UPDATE SET
                  model = EXCLUDED.model,
                  dim = EXCLUDED.dim,
                  embedding = EXCLUDED.embedding,
                  sparse = NULL
                """
            ),
            {
                "chunk_id": chunk_id,
                "tenant_id": tenant_id,
                "collection_id": collection_id,
                "model": model,
                "dim": dim,
                "embedding": vec_literal,
            },
        )


def mark_document_ready(
    conn: Connection,
    *,
    document_id: str,
    tenant_id: str,
) -> None:
    conn.execute(
        text(
            """
            UPDATE documents
            SET status = 'ready', finalized_at = COALESCE(finalized_at, now())
            WHERE id = :document_id AND tenant_id = :tenant_id
            """
        ),
        {"document_id": document_id, "tenant_id": tenant_id},
    )


def bump_collection_index_version(
    conn: Connection,
    *,
    collection_id: str,
    tenant_id: str,
) -> None:
    conn.execute(
        text(
            """
            UPDATE collections
            SET index_version = index_version + 1
            WHERE id = :collection_id AND tenant_id = :tenant_id
            """
        ),
        {"collection_id": collection_id, "tenant_id": tenant_id},
    )


def audit_embed(
    conn: Connection,
    *,
    tenant_id: str,
    document_id: str,
    chunk_count: int,
    model: str,
) -> None:
    write_audit_event(
        conn,
        tenant_id=tenant_id,
        actor="system",
        action="document.embed",
        target_kind="document",
        target_id=document_id,
        payload={
            "chunk_count": chunk_count,
            "model": model,
            "dim": EMBED_DIM,
            "sparse_stored": False,
        },
    )


def mark_document_failed(
    conn: Connection,
    *,
    document_id: str,
    tenant_id: str,
) -> None:
    conn.execute(
        text(
            """
            UPDATE documents
            SET status = 'failed'
            WHERE id = :document_id AND tenant_id = :tenant_id
            """
        ),
        {"document_id": document_id, "tenant_id": tenant_id},
    )


def audit_embed_failed(
    conn: Connection,
    *,
    tenant_id: str,
    document_id: str,
    error_type: str,
) -> None:
    write_audit_event(
        conn,
        tenant_id=tenant_id,
        actor="system",
        action="document.embed_failed",
        target_kind="document",
        target_id=document_id,
        payload={"error_type": error_type},
    )


def run_embed_document(  # noqa: PLR0913 — explicit injectable seams for TDD
    *,
    document_id: str,
    tenant_id: str,
    force: bool = False,
    settings: Settings | None = None,
    tei: TeiClient | None = None,
    engine: Engine | None = None,
    load_chunks: LoadChunksFn | None = None,
    upsert: UpsertFn | None = None,
    mark_ready: MarkReadyFn | None = None,
    bump_index: BumpIndexFn | None = None,
    audit: AuditFn | None = None,
) -> str:
    """Embed approved chunks for one document. Returns ``embedded`` or ``noop``."""
    cfg = settings or get_settings()
    client = tei or TeiClient(base_url=cfg.sift_tei_url, model=cfg.sift_tei_model)
    load_fn = load_chunks or load_chunks_needing_embed
    upsert_fn = upsert or upsert_chunk_embeddings
    mark_fn = mark_ready or mark_document_ready
    bump_fn = bump_index or bump_collection_index_version
    audit_fn = audit or audit_embed

    # Unit-test path: injectable helpers without a DB connection.
    if engine is None and load_chunks is not None:
        return _run_injected(
            document_id=document_id,
            tenant_id=tenant_id,
            force=force,
            tei=client,
            settings=cfg,
            load_fn=load_fn,
            upsert_fn=upsert_fn,
            mark_fn=mark_fn,
            bump_fn=bump_fn,
            audit_fn=audit_fn,
        )

    owns_engine = engine is None
    eng = engine or create_engine(sync_dsn(cfg))
    try:
        with eng.begin() as conn:
            conn.execute(text("SET LOCAL ROLE sift_admin"))
            chunks = load_fn(
                conn,
                document_id=document_id,
                tenant_id=tenant_id,
                force=force,
            )
            if not chunks:
                mark_fn(conn, document_id=document_id, tenant_id=tenant_id)
                return "noop"
            collection_id = str(chunks[0]["collection_id"])
            chunk_ids = [str(c["id"]) for c in chunks]
            texts = [str(c["text_contextualized"]) for c in chunks]

        # Network I/O outside the DB transaction (code-security §10).
        try:
            vectors = client.embed(texts, batch_size=EMBED_BATCH)
        except Exception as exc:
            with eng.begin() as conn:
                conn.execute(text("SET LOCAL ROLE sift_admin"))
                mark_document_failed(conn, document_id=document_id, tenant_id=tenant_id)
                audit_embed_failed(
                    conn,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    error_type=type(exc).__name__,
                )
            raise

        if len(vectors) != len(chunks):
            msg = f"TEI returned {len(vectors)} vectors for {len(chunks)} chunks"
            with eng.begin() as conn:
                conn.execute(text("SET LOCAL ROLE sift_admin"))
                mark_document_failed(conn, document_id=document_id, tenant_id=tenant_id)
                audit_embed_failed(
                    conn,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    error_type="RuntimeError",
                )
            raise RuntimeError(msg)

        with eng.begin() as conn:
            conn.execute(text("SET LOCAL ROLE sift_admin"))
            upsert_fn(
                conn,
                tenant_id=tenant_id,
                collection_id=collection_id,
                chunk_ids=chunk_ids,
                embeddings=vectors,
                sparse=None,
            )
            mark_fn(conn, document_id=document_id, tenant_id=tenant_id)
            bump_fn(conn, collection_id=collection_id, tenant_id=tenant_id)
            audit_fn(
                conn,
                tenant_id=tenant_id,
                document_id=document_id,
                chunk_count=len(chunks),
                model=cfg.sift_tei_model,
            )
            return "embedded"
    finally:
        if owns_engine:
            eng.dispose()


def _run_injected(  # noqa: PLR0913 — mirrors injectable seams for unit tests
    *,
    document_id: str,
    tenant_id: str,
    force: bool,
    tei: TeiClient,
    settings: Settings,
    load_fn: LoadChunksFn,
    upsert_fn: UpsertFn,
    mark_fn: MarkReadyFn,
    bump_fn: BumpIndexFn,
    audit_fn: AuditFn,
) -> str:
    chunks = load_fn(document_id=document_id, tenant_id=tenant_id, force=force)
    if not chunks:
        mark_fn(document_id=document_id, tenant_id=tenant_id)
        return "noop"
    collection_id = str(chunks[0]["collection_id"])
    texts = [str(c["text_contextualized"]) for c in chunks]
    vectors = tei.embed(texts, batch_size=EMBED_BATCH)
    upsert_fn(
        tenant_id=tenant_id,
        collection_id=collection_id,
        chunk_ids=[str(c["id"]) for c in chunks],
        embeddings=vectors,
        sparse=None,
    )
    mark_fn(document_id=document_id, tenant_id=tenant_id)
    bump_fn(collection_id=collection_id, tenant_id=tenant_id)
    audit_fn(
        tenant_id=tenant_id,
        document_id=document_id,
        chunk_count=len(chunks),
        model=settings.sift_tei_model,
        action="document.embed",
        payload={
            "chunk_count": len(chunks),
            "sparse_stored": False,
        },
    )
    return "embedded"
