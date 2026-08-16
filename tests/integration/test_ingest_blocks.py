"""Blocks table RLS + ingest persistence (requires Postgres)."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from sift.parse import DigitalPdfParser, ParseConfig
from sift_api.ingest import run_ingest_document
from sift_core.db import tenant_guc_statements
from sift_core.ids import IdKind, new_id

CORPUS = Path(__file__).resolve().parents[2] / "evals" / "corpus"
DIGITAL_PDF = sorted(CORPUS.glob("digital-*.pdf"))[0]


def _apply_tenant(conn: object, tenant_id: str) -> None:
    for statement in tenant_guc_statements(tenant_id):
        conn.execute(text(statement))  # type: ignore[attr-defined]


def test_ingest_parse_persists_blocks_and_sets_indexing(
    migrated_db: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "sift_api.ingest_parse.enqueue_embed_document",
        lambda **_kwargs: None,
    )
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    collection_id = new_id(IdKind.COLLECTION)
    document_id = new_id(IdKind.DOCUMENT)
    job_id = new_id(IdKind.JOB)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'Org', 'org')"),
            {"id": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug)
                VALUES (:id, :org, 'T', 't')
                """
            ),
            {"id": tenant_id, "org": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO collections (id, tenant_id, name, slug)
                VALUES (:id, :tid, 'C', 'c')
                """
            ),
            {"id": collection_id, "tid": tenant_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO documents (
                  id, tenant_id, collection_id, title, slug, source_uri, source_mime,
                  source_bytes, source_sha256, status, created_by
                ) VALUES (
                  :id, :tid, :cid, 'Doc', 'doc', 'seaweed://bucket/key.pdf', 'application/pdf',
                  1, 'abc', 'queued', 'test'
                )
                """
            ),
            {"id": document_id, "tid": tenant_id, "cid": collection_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO jobs (
                  id, tenant_id, collection_id, document_id, kind, status, progress
                ) VALUES (
                  :id, :tid, :cid, :did, 'ingest', 'queued', 0
                )
                """
            ),
            {
                "id": job_id,
                "tid": tenant_id,
                "cid": collection_id,
                "did": document_id,
            },
        )

    status = run_ingest_document(
        document_id=document_id,
        job_id=job_id,
        tenant_id=tenant_id,
        source_path=DIGITAL_PDF,
        parser=DigitalPdfParser(),
        parse_config=ParseConfig(),
    )
    assert status == "indexing"

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_app"))
        _apply_tenant(conn, tenant_id)
        blocks = (
            conn.execute(
                text(
                    """
                    SELECT ordinal, block_type, review_state, provenance
                    FROM blocks
                    WHERE document_id = :did
                    ORDER BY ordinal
                    """
                ),
                {"did": document_id},
            )
            .mappings()
            .all()
        )
        doc = (
            conn.execute(
                text("SELECT status, needs_review_count, page_count FROM documents WHERE id = :id"),
                {"id": document_id},
            )
            .mappings()
            .one()
        )

    assert len(blocks) > 0
    assert [b["ordinal"] for b in blocks] == list(range(len(blocks)))
    assert all(b["block_type"] == "paragraph" for b in blocks)
    assert all(b["review_state"] == "approved" for b in blocks)
    assert all(b["provenance"]["extractor"] == "digital-pdf" for b in blocks)
    assert doc["status"] == "indexing"
    assert doc["needs_review_count"] == 0
    assert doc["page_count"] >= 1
    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_app"))
        _apply_tenant(conn, tenant_id)
        chunk_n = conn.execute(
            text("SELECT count(*) FROM chunks WHERE document_id = :id"),
            {"id": document_id},
        ).scalar_one()
    assert int(chunk_n) > 0


def test_blocks_rls_hides_other_tenant(migrated_db: Engine) -> None:
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_a = new_id(IdKind.TENANT)
    tenant_b = new_id(IdKind.TENANT)
    col_a = new_id(IdKind.COLLECTION)
    doc_a = new_id(IdKind.DOCUMENT)
    job_a = new_id(IdKind.JOB)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'Org', 'org-rls')"),
            {"id": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug)
                VALUES
                  (:a, :org, 'A', 'a'),
                  (:b, :org, 'B', 'b')
                """
            ),
            {"a": tenant_a, "b": tenant_b, "org": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO collections (id, tenant_id, name, slug)
                VALUES (:id, :tid, 'C', 'c')
                """
            ),
            {"id": col_a, "tid": tenant_a},
        )
        conn.execute(
            text(
                """
                INSERT INTO documents (
                  id, tenant_id, collection_id, title, slug, source_uri, source_mime,
                  source_bytes, source_sha256, status, created_by
                ) VALUES (
                  :id, :tid, :cid, 'Doc', 'doc', 'seaweed://bucket/key.pdf', 'application/pdf',
                  1, 'abc', 'queued', 'test'
                )
                """
            ),
            {"id": doc_a, "tid": tenant_a, "cid": col_a},
        )
        conn.execute(
            text(
                """
                INSERT INTO jobs (
                  id, tenant_id, collection_id, document_id, kind, status, progress
                ) VALUES (
                  :id, :tid, :cid, :did, 'ingest', 'queued', 0
                )
                """
            ),
            {"id": job_a, "tid": tenant_a, "cid": col_a, "did": doc_a},
        )

    run_ingest_document(
        document_id=doc_a,
        job_id=job_a,
        tenant_id=tenant_a,
        source_path=DIGITAL_PDF,
    )

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_app"))
        _apply_tenant(conn, tenant_b)
        visible = conn.execute(text("SELECT count(*) FROM blocks")).scalar_one()
        assert visible == 0

        _apply_tenant(conn, tenant_a)
        visible_a = conn.execute(text("SELECT count(*) FROM blocks")).scalar_one()
        assert visible_a > 0
