"""RLS + shape checks for chunk_embeddings (Phase 3 §4.10)."""

from __future__ import annotations

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError

from sift_core.db import tenant_guc_statements
from sift_core.ids import IdKind, new_id

pytestmark = pytest.mark.integration


def _apply_tenant_context(connection: Connection, tenant_id: str) -> None:
    for statement in tenant_guc_statements(tenant_id):
        connection.execute(text(statement))


def test_chunk_embeddings_table_shape_when_migrated(migrated_db: Engine) -> None:
    with migrated_db.connect() as conn:
        cols = {
            row[0]: row[1]
            for row in conn.execute(
                text(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'chunk_embeddings'
                    """
                )
            )
        }
        assert "chunk_id" in cols
        assert "tenant_id" in cols
        assert "collection_id" in cols
        assert "model" in cols
        assert "dim" in cols
        assert "embedding" in cols
        assert "sparse" in cols

        indexes = {
            row[0]
            for row in conn.execute(
                text(
                    """
                    SELECT indexname FROM pg_indexes
                    WHERE schemaname = 'public' AND tablename = 'chunk_embeddings'
                    """
                )
            )
        }
        assert "chunk_embeddings_vec_idx" in indexes
        assert "chunk_embeddings_collection_idx" in indexes
        assert "chunk_embeddings_tenant_idx" in indexes

        rls = conn.execute(
            text(
                """
                SELECT relrowsecurity, relforcerowsecurity
                FROM pg_class
                WHERE relname = 'chunk_embeddings'
                """
            )
        ).one()
        assert rls[0] is True
        assert rls[1] is True


def test_chunk_embeddings_rls_hides_other_tenant(migrated_db: Engine) -> None:
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_a = new_id(IdKind.TENANT)
    tenant_b = new_id(IdKind.TENANT)
    col_a = new_id(IdKind.COLLECTION)
    col_b = new_id(IdKind.COLLECTION)
    doc_a = new_id(IdKind.DOCUMENT)
    doc_b = new_id(IdKind.DOCUMENT)
    chunk_a = new_id(IdKind.CHUNK)
    chunk_b = new_id(IdKind.CHUNK)
    chunk_b_extra = new_id(IdKind.CHUNK)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'Org', 'org')"),
            {"id": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug) VALUES
                  (:a, :org, 'A', 'a'), (:b, :org, 'B', 'b')
                """
            ),
            {"a": tenant_a, "b": tenant_b, "org": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO collections (id, tenant_id, name, slug) VALUES
                  (:ca, :a, 'CA', 'ca'), (:cb, :b, 'CB', 'cb')
                """
            ),
            {"ca": col_a, "cb": col_b, "a": tenant_a, "b": tenant_b},
        )
        conn.execute(
            text(
                """
                INSERT INTO documents (
                  id, tenant_id, collection_id, title, slug,
                  source_uri, source_mime, source_bytes, source_sha256,
                  status, created_by
                ) VALUES
                  (:da, :a, :ca, 'DA', 'da', 's://a', 'application/pdf', 1, 'aa',
                   'ready', 'u'),
                  (:db, :b, :cb, 'DB', 'db', 's://b', 'application/pdf', 1, 'bb',
                   'ready', 'u')
                """
            ),
            {
                "da": doc_a,
                "db": doc_b,
                "a": tenant_a,
                "b": tenant_b,
                "ca": col_a,
                "cb": col_b,
            },
        )
        for chunk_id, tenant_id, doc_id, collection_id in (
            (chunk_a, tenant_a, doc_a, col_a),
            (chunk_b, tenant_b, doc_b, col_b),
        ):
            conn.execute(
                text(
                    """
                    INSERT INTO chunks (
                      id, tenant_id, document_id, collection_id, ordinal,
                      text_raw, text_contextualized, token_count, chunk_type
                    ) VALUES (
                      :id, :tid, :did, :cid, 0, 'raw', 'ctx', 1, 'text'
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
            conn.execute(
                text(
                    """
                    INSERT INTO chunk_embeddings (
                      chunk_id, tenant_id, collection_id, model, dim, embedding, sparse
                    ) VALUES (
                      :id, :tid, :cid, 'bge-m3', 1024,
                      (SELECT array_agg(0.0)::vector FROM generate_series(1, 1024)),
                      '{}'::jsonb
                    )
                    """
                ),
                {"id": chunk_id, "tid": tenant_id, "cid": collection_id},
            )
        conn.execute(
            text(
                """
                INSERT INTO chunks (
                  id, tenant_id, document_id, collection_id, ordinal,
                  text_raw, text_contextualized, token_count, chunk_type
                ) VALUES (
                  :id, :tid, :did, :cid, 1, 'raw2', 'ctx2', 1, 'text'
                )
                """
            ),
            {
                "id": chunk_b_extra,
                "tid": tenant_b,
                "did": doc_b,
                "cid": col_b,
            },
        )

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_app"))
        _apply_tenant_context(conn, tenant_a)
        visible = (
            conn.execute(text("SELECT chunk_id FROM chunk_embeddings ORDER BY chunk_id"))
            .scalars()
            .all()
        )
        assert visible == [chunk_a]

        updated = conn.execute(
            text("UPDATE chunk_embeddings SET model = 'x' WHERE chunk_id = :id"),
            {"id": chunk_b},
        ).rowcount
        assert updated == 0

        deleted = conn.execute(
            text("DELETE FROM chunk_embeddings WHERE chunk_id = :id"),
            {"id": chunk_b},
        ).rowcount
        assert deleted == 0

        with pytest.raises(DBAPIError):
            conn.execute(
                text(
                    """
                    INSERT INTO chunk_embeddings (
                      chunk_id, tenant_id, collection_id, model, dim, embedding, sparse
                    ) VALUES (
                      :id, :tid, :cid, 'bge-m3', 1024,
                      (SELECT array_agg(0.0)::vector FROM generate_series(1, 1024)),
                      '{}'::jsonb
                    )
                    """
                ),
                {"id": chunk_b_extra, "tid": tenant_b, "cid": col_b},
            )
