"""Document content streaming for review PDF viewer (Phase 2 §4.4)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

from sift_api import db as db_mod
from sift_api.main import app
from sift_api.settings import get_settings
from sift_core.auth.api_keys import mint_api_key
from sift_core.ids import IdKind, new_id

PEPPER = "phase2-content-pepper-do-not-use-prod"
_MINIMAL_PDF = b"%PDF-1.1\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


@pytest.fixture
def api_client(migrated_db: Engine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    raw = os.environ.get("SIFT_PG_DSN") or "postgresql+psycopg://sift:sift@127.0.0.1:5432/sift"
    if raw.startswith("postgresql+psycopg://"):
        async_dsn = "postgresql+asyncpg://" + raw.removeprefix("postgresql+psycopg://")
    elif raw.startswith("postgresql://"):
        async_dsn = "postgresql+asyncpg://" + raw.removeprefix("postgresql://")
    else:
        async_dsn = raw
    monkeypatch.setenv("SIFT_API_KEY_PEPPER", PEPPER)
    monkeypatch.setenv("SIFT_PG_DSN", async_dsn)
    get_settings.cache_clear()
    db_mod._STATE.engine = None
    db_mod._STATE.session_factory = None
    with TestClient(app) as client:
        yield client
    get_settings.cache_clear()
    db_mod._STATE.engine = None
    db_mod._STATE.session_factory = None


def _seed_doc_with_pdf(engine: Engine, pdf_path: Path) -> tuple[str, str, str]:
    """Return (write_raw, read_raw, document_id). Uses file:// source for tests."""
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    collection_id = new_id(IdKind.COLLECTION)
    document_id = new_id(IdKind.DOCUMENT)
    write_key = mint_api_key(PEPPER.encode())
    read_key = mint_api_key(PEPPER.encode())
    now = datetime.now(UTC)
    source_uri = f"file://{pdf_path.resolve()}"
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text(
                "INSERT INTO organizations (id, name, slug, created_at) "
                "VALUES (:id, 'C', :slug, :now)"
            ),
            {"id": org_id, "slug": f"c-{org_id[-8:].lower()}", "now": now},
        )
        conn.execute(
            text(
                "INSERT INTO tenants (id, organization_id, name, slug, created_at) "
                "VALUES (:id, :org, 'C', :slug, :now)"
            ),
            {
                "id": tenant_id,
                "org": org_id,
                "slug": f"t-{tenant_id[-8:].lower()}",
                "now": now,
            },
        )
        for name, minted, scopes in (
            ("write", write_key, ["documents:read", "documents:write"]),
            ("search", read_key, ["search"]),
        ):
            conn.execute(
                text(
                    """
                    INSERT INTO api_keys (
                      id, tenant_id, name, hash, hash_version, prefix, scopes,
                      created_by, created_at
                    ) VALUES (
                      :id, :tenant_id, :name, :hash, 1, :prefix, :scopes, 'test', :now
                    )
                    """
                ),
                {
                    "id": new_id(IdKind.API_KEY),
                    "tenant_id": tenant_id,
                    "name": name,
                    "hash": minted.hash,
                    "prefix": minted.prefix,
                    "scopes": scopes,
                    "now": now,
                },
            )
        conn.execute(
            text(
                """
                INSERT INTO collections (id, tenant_id, name, slug, created_at)
                VALUES (:id, :tid, 'C', :slug, :now)
                """
            ),
            {
                "id": collection_id,
                "tid": tenant_id,
                "slug": f"c-{collection_id[-8:].lower()}",
                "now": now,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO documents (
                  id, tenant_id, collection_id, title, slug, source_uri, source_mime,
                  source_bytes, source_sha256, status, needs_review_count, created_by,
                  created_at
                ) VALUES (
                  :id, :tid, :cid, 'Doc', :slug, :uri, 'application/pdf',
                  :nbytes, :sha, 'ready_for_review', 0, 'test', :now
                )
                """
            ),
            {
                "id": document_id,
                "tid": tenant_id,
                "cid": collection_id,
                "slug": f"d-{document_id[-8:].lower()}",
                "uri": source_uri,
                "nbytes": len(_MINIMAL_PDF),
                "sha": "c" * 64,
                "now": now,
            },
        )
    return write_key.raw, read_key.raw, document_id


@pytest.mark.integration
def test_document_content_unauthenticated_returns_401(
    api_client: TestClient, migrated_db: Engine, tmp_path: Path
) -> None:
    pdf = tmp_path / "d.pdf"
    pdf.write_bytes(_MINIMAL_PDF)
    _w, _r, document_id = _seed_doc_with_pdf(migrated_db, pdf)
    response = api_client.get(f"/v1/documents/{document_id}/content")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
def test_document_content_wrong_scope_returns_403(
    api_client: TestClient, migrated_db: Engine, tmp_path: Path
) -> None:
    pdf = tmp_path / "d.pdf"
    pdf.write_bytes(_MINIMAL_PDF)
    _w, search_raw, document_id = _seed_doc_with_pdf(migrated_db, pdf)
    response = api_client.get(
        f"/v1/documents/{document_id}/content",
        headers={"X-Api-Key": search_raw},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.integration
def test_document_content_wrong_tenant_returns_404(
    api_client: TestClient, migrated_db: Engine, tmp_path: Path
) -> None:
    pdf = tmp_path / "d.pdf"
    pdf.write_bytes(_MINIMAL_PDF)
    write_raw, _r, _document_id = _seed_doc_with_pdf(migrated_db, pdf)
    foreign = new_id(IdKind.DOCUMENT)
    response = api_client.get(
        f"/v1/documents/{foreign}/content",
        headers={"X-Api-Key": write_raw},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
def test_document_content_streams_pdf(
    api_client: TestClient, migrated_db: Engine, tmp_path: Path
) -> None:
    pdf = tmp_path / "d.pdf"
    pdf.write_bytes(_MINIMAL_PDF)
    write_raw, _r, document_id = _seed_doc_with_pdf(migrated_db, pdf)
    response = api_client.get(
        f"/v1/documents/{document_id}/content",
        headers={"X-Api-Key": write_raw},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
