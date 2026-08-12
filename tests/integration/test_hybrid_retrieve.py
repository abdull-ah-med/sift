"""Integration: dense store + hybrid (BM25 mocked) against Postgres."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from sift_api.embed import EMBED_DIM, run_embed_document
from sift_core.ids import IdKind, new_id
from sift_retrieve.hybrid import HybridRetriever, RetrieveHit
from sift_retrieve.store.pgvector import PgvectorDenseStore

pytestmark = pytest.mark.integration


def _seed(engine: Engine) -> tuple[str, str, str, str]:
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    collection_id = new_id(IdKind.COLLECTION)
    doc_id = new_id(IdKind.DOCUMENT)
    chunk_id = new_id(IdKind.CHUNK)
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("INSERT INTO organizations (id, name, slug, created_at) VALUES (:id,'O',:s,:n)"),
            {"id": org_id, "s": f"o-{org_id[-8:].lower()}", "n": now},
        )
        conn.execute(
            text(
                "INSERT INTO tenants (id, organization_id, name, slug, created_at) "
                "VALUES (:id,:org,'T',:s,:n)"
            ),
            {"id": tenant_id, "org": org_id, "s": f"t-{tenant_id[-8:].lower()}", "n": now},
        )
        conn.execute(
            text(
                "INSERT INTO collections (id, tenant_id, name, slug, created_at) "
                "VALUES (:id,:tid,'C',:s,:n)"
            ),
            {
                "id": collection_id,
                "tid": tenant_id,
                "s": f"c-{collection_id[-8:].lower()}",
                "n": now,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO documents (
                  id, tenant_id, collection_id, title, slug,
                  source_uri, source_mime, source_bytes, source_sha256,
                  status, created_by, created_at
                ) VALUES (
                  :id, :tid, :cid, 'D', :slug, 's://x', 'application/pdf', 1, :sha,
                  'indexing', 'u', :n
                )
                """
            ),
            {
                "id": doc_id,
                "tid": tenant_id,
                "cid": collection_id,
                "slug": f"d-{doc_id[-8:].lower()}",
                "sha": f"sha-{doc_id[-12:]}",
                "n": now,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO chunks (
                  id, tenant_id, document_id, collection_id, ordinal,
                  text_raw, text_contextualized, token_count, chunk_type, review_state
                ) VALUES (
                  :id, :tid, :did, :cid, 0, 'refund policy text',
                  'refund policy for EU customers', 4, 'text', 'approved'
                )
                """
            ),
            {"id": chunk_id, "tid": tenant_id, "did": doc_id, "cid": collection_id},
        )
    return tenant_id, collection_id, doc_id, chunk_id


def test_pgvector_dense_search_returns_tenant_chunk(migrated_db: Engine) -> None:
    tenant_id, collection_id, doc_id, chunk_id = _seed(migrated_db)
    tei = MagicMock()
    tei.embed.return_value = [[0.02] * EMBED_DIM]
    assert (
        run_embed_document(
            document_id=doc_id,
            tenant_id=tenant_id,
            tei=tei,
            engine=migrated_db,
        )
        == "embedded"
    )

    with migrated_db.connect() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        store = PgvectorDenseStore(conn)
        hits = store.search(
            query_vector=[0.02] * EMBED_DIM,
            tenant_id=tenant_id,
            collection_id=collection_id,
            limit=5,
        )
    assert any(h.chunk_id == chunk_id for h in hits)


def test_hybrid_with_mocked_bm25(migrated_db: Engine) -> None:
    tenant_id, collection_id, doc_id, chunk_id = _seed(migrated_db)
    tei = MagicMock()
    tei.embed.return_value = [[0.03] * EMBED_DIM]
    run_embed_document(
        document_id=doc_id,
        tenant_id=tenant_id,
        tei=tei,
        engine=migrated_db,
    )

    bm25 = MagicMock()
    bm25.search.return_value = [
        RetrieveHit(chunk_id=chunk_id, document_id=doc_id, score=5.0),
    ]
    reranker = MagicMock()
    reranker.rerank.return_value = [(chunk_id, 0.95)]

    with migrated_db.connect() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        dense = PgvectorDenseStore(conn)
        retriever = HybridRetriever(
            dense=dense,
            bm25=bm25,
            tei=tei,
            reranker=reranker,
            load_texts=lambda _ids: {chunk_id: "refund policy for EU customers"},
        )
        hits = retriever.retrieve(
            query="refund",
            tenant_id=tenant_id,
            collection_id=collection_id,
            top_k=5,
            rerank=True,
        )
    assert hits[0].chunk_id == chunk_id
    assert hits[0].rerank_score == 0.95
