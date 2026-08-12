"""LangGraph interrupt/resume via Postgres checkpointer + HTTP security."""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

from sift_api import db as db_mod
from sift_api.checkpointer import close_postgres_checkpointer
from sift_api.main import app
from sift_api.settings import get_settings
from sift_core.auth.api_keys import mint_api_key
from sift_core.ids import IdKind, new_id

PEPPER = "phase2-langgraph-pepper-do-not-use-prod"


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


def _seed_doc_with_needs_review(engine: Engine) -> tuple[str, str, str, str]:
    """Return (write_raw, read_raw, document_id, needs_block_id)."""
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    collection_id = new_id(IdKind.COLLECTION)
    document_id = new_id(IdKind.DOCUMENT)
    needs_id = new_id(IdKind.BLOCK)
    write_key = mint_api_key(PEPPER.encode())
    read_key = mint_api_key(PEPPER.encode())
    now = datetime.now(UTC)
    provenance = json.dumps(
        {
            "page_no": 1,
            "bbox": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
            "extractor": "digital-pdf",
            "model_version": "pypdfium2",
        }
    )
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text(
                "INSERT INTO organizations (id, name, slug, created_at) "
                "VALUES (:id, 'LG', :slug, :now)"
            ),
            {"id": org_id, "slug": f"lg-{org_id[-8:].lower()}", "now": now},
        )
        conn.execute(
            text(
                "INSERT INTO tenants (id, organization_id, name, slug, created_at) "
                "VALUES (:id, :org, 'LG', :slug, :now)"
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
            ("read", read_key, ["documents:read"]),
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
                  :id, :tid, :cid, 'Doc', :slug, 'seaweed://b/k.pdf', 'application/pdf',
                  1, :sha, 'ready_for_review', 1, 'test', :now
                )
                """
            ),
            {
                "id": document_id,
                "tid": tenant_id,
                "cid": collection_id,
                "slug": f"d-{document_id[-8:].lower()}",
                "sha": "b" * 64,
                "now": now,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO blocks (
                  id, tenant_id, document_id, ordinal, block_type, text,
                  provenance, confidence, review_state, version
                ) VALUES (
                  :id, :tid, :did, 0, 'paragraph', 'needs work',
                  CAST(:prov AS jsonb), 0.4, 'needs_review', 1
                )
                """
            ),
            {
                "id": needs_id,
                "tid": tenant_id,
                "did": document_id,
                "prov": provenance,
            },
        )
    return write_key.raw, read_key.raw, document_id, needs_id


@pytest.mark.integration
def test_review_start_unauthenticated_returns_401(
    api_client: TestClient, migrated_db: Engine
) -> None:
    _write, _read, document_id, _bid = _seed_doc_with_needs_review(migrated_db)
    response = api_client.post(f"/v1/documents/{document_id}/review/start")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
def test_review_start_wrong_scope_returns_403(api_client: TestClient, migrated_db: Engine) -> None:
    _write, read_raw, document_id, _bid = _seed_doc_with_needs_review(migrated_db)
    response = api_client.post(
        f"/v1/documents/{document_id}/review/start",
        headers={"X-Api-Key": read_raw},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.integration
def test_review_start_wrong_tenant_returns_404(api_client: TestClient, migrated_db: Engine) -> None:
    write_raw, _read, _document_id, _bid = _seed_doc_with_needs_review(migrated_db)
    foreign_doc = new_id(IdKind.DOCUMENT)
    response = api_client.post(
        f"/v1/documents/{foreign_doc}/review/start",
        headers={"X-Api-Key": write_raw},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
def test_review_resume_unauthenticated_returns_401(
    api_client: TestClient, migrated_db: Engine
) -> None:
    _write, _read, document_id, needs_id = _seed_doc_with_needs_review(migrated_db)
    response = api_client.post(
        f"/v1/documents/{document_id}/review/resume",
        json={"decisions": [{"block_id": needs_id, "action": "approve"}]},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.integration
def test_review_resume_wrong_scope_returns_403(api_client: TestClient, migrated_db: Engine) -> None:
    _write, read_raw, document_id, needs_id = _seed_doc_with_needs_review(migrated_db)
    response = api_client.post(
        f"/v1/documents/{document_id}/review/resume",
        headers={"X-Api-Key": read_raw},
        json={"decisions": [{"block_id": needs_id, "action": "approve"}]},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.integration
def test_review_resume_wrong_tenant_returns_404(
    api_client: TestClient, migrated_db: Engine
) -> None:
    write_raw, _read, _document_id, needs_id = _seed_doc_with_needs_review(migrated_db)
    foreign_doc = new_id(IdKind.DOCUMENT)
    response = api_client.post(
        f"/v1/documents/{foreign_doc}/review/resume",
        headers={"X-Api-Key": write_raw},
        json={"decisions": [{"block_id": needs_id, "action": "approve"}]},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.integration
def test_review_interrupt_survives_api_restart(api_client: TestClient, migrated_db: Engine) -> None:
    """Start → interrupt, drop in-process state, resume via Postgres checkpointer."""
    write_raw, _read, document_id, needs_id = _seed_doc_with_needs_review(migrated_db)
    headers = {"X-Api-Key": write_raw}

    started = api_client.post(f"/v1/documents/{document_id}/review/start", headers=headers)
    assert started.status_code == HTTPStatus.OK
    body = started.json()
    assert body["status"] == "pending_review"
    assert needs_id in body["pending_block_ids"]
    assert body["thread_id"] == f"doc-review:{document_id}"

    # Simulate API process restart: close pooled checkpointer + SQLAlchemy engine.
    api_client.portal.call(close_postgres_checkpointer)
    api_client.portal.call(db_mod.dispose_engine)
    get_settings.cache_clear()

    resumed = api_client.post(
        f"/v1/documents/{document_id}/review/resume",
        headers=headers,
        json={
            "decisions": [
                {"block_id": needs_id, "action": "approve"},
            ]
        },
    )
    assert resumed.status_code == HTTPStatus.OK
    done = resumed.json()
    assert done["status"] == "complete"
    assert done["pending_block_ids"] == []
