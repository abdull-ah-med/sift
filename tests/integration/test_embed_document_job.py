"""Integration: embed_document upserts dense vectors (mocked TEI)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from sift_api.embed import EMBED_DIM, run_embed_document
from sift_core.ids import IdKind, new_id

pytestmark = pytest.mark.integration


def _seed_doc_with_chunk(engine: Engine) -> tuple[str, str, str, str]:
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
            {
                "id": tenant_id,
                "org": org_id,
                "s": f"t-{tenant_id[-8:].lower()}",
                "n": now,
            },
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
                  :id, :tid, :cid, 'D', :slug,
                  's://x', 'application/pdf', 1, :sha,
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
                  :id, :tid, :did, :cid, 0, 'raw', 'ctx text', 2, 'text', 'approved'
                )
                """
            ),
            {
                "id": chunk_id,
                "tid": tenant_id,
                "did": doc_id,
                "cid": collection_id,
            },
        )
    return tenant_id, collection_id, doc_id, chunk_id


def test_run_embed_document_persists_dense_and_ready(migrated_db: Engine) -> None:
    tenant_id, collection_id, doc_id, chunk_id = _seed_doc_with_chunk(migrated_db)
    tei = MagicMock()
    tei.embed.return_value = [[0.05] * 1024]

    result = run_embed_document(
        document_id=doc_id,
        tenant_id=tenant_id,
        tei=tei,
        engine=migrated_db,
    )
    assert result == "embedded"

    with migrated_db.connect() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        row = (
            conn.execute(
                text(
                    """
                    SELECT model, dim, sparse, embedding::text
                    FROM chunk_embeddings WHERE chunk_id = :id
                    """
                ),
                {"id": chunk_id},
            )
            .mappings()
            .one()
        )
        assert row["model"] == "bge-m3"
        assert row["dim"] == EMBED_DIM
        assert row["sparse"] is None
        status = conn.execute(
            text("SELECT status FROM documents WHERE id = :id"),
            {"id": doc_id},
        ).scalar_one()
        assert status == "ready"
        version = conn.execute(
            text("SELECT index_version FROM collections WHERE id = :id"),
            {"id": collection_id},
        ).scalar_one()
        assert int(version) >= 1

    # Idempotent second run
    tei.embed.reset_mock()
    result2 = run_embed_document(
        document_id=doc_id,
        tenant_id=tenant_id,
        tei=tei,
        engine=migrated_db,
    )
    assert result2 == "noop"
    tei.embed.assert_not_called()
