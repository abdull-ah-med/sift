"""HITL review API against live Postgres."""

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
from sift_api.main import app
from sift_api.settings import get_settings
from sift_core.auth.api_keys import mint_api_key
from sift_core.ids import IdKind, new_id

PEPPER = "phase2-review-pepper-do-not-use-prod"


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


def _seed_review_fixture(engine: Engine) -> tuple[str, str, str, str]:
    """Return (raw_key, document_id, needs_review_block_id, approved_block_id)."""
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    collection_id = new_id(IdKind.COLLECTION)
    document_id = new_id(IdKind.DOCUMENT)
    needs_id = new_id(IdKind.BLOCK)
    approved_id = new_id(IdKind.BLOCK)
    minted = mint_api_key(PEPPER.encode())
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
                "VALUES (:id, 'R', :slug, :now)"
            ),
            {"id": org_id, "slug": f"r-{org_id[-8:].lower()}", "now": now},
        )
        conn.execute(
            text(
                "INSERT INTO tenants (id, organization_id, name, slug, created_at) "
                "VALUES (:id, :org, 'R', :slug, :now)"
            ),
            {
                "id": tenant_id,
                "org": org_id,
                "slug": f"t-{tenant_id[-8:].lower()}",
                "now": now,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO api_keys (
                  id, tenant_id, name, hash, hash_version, prefix, scopes,
                  created_by, created_at
                ) VALUES (
                  :id, :tenant_id, 'write', :hash, 1, :prefix, :scopes, 'test', :now
                )
                """
            ),
            {
                "id": new_id(IdKind.API_KEY),
                "tenant_id": tenant_id,
                "hash": minted.hash,
                "prefix": minted.prefix,
                "scopes": ["documents:read", "documents:write"],
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
                "sha": "a" * 64,
                "now": now,
            },
        )
        for block_id, ordinal, state, body in (
            (needs_id, 0, "needs_review", "needs work"),
            (approved_id, 1, "approved", "already good"),
        ):
            conn.execute(
                text(
                    """
                    INSERT INTO blocks (
                      id, tenant_id, document_id, ordinal, block_type, text,
                      provenance, confidence, review_state, version
                    ) VALUES (
                      :id, :tid, :did, :ord, 'paragraph', :text,
                      CAST(:prov AS jsonb), 0.5, :state, 1
                    )
                    """
                ),
                {
                    "id": block_id,
                    "tid": tenant_id,
                    "did": document_id,
                    "ord": ordinal,
                    "text": body,
                    "prov": provenance,
                    "state": state,
                },
            )
    return minted.raw, document_id, needs_id, approved_id


def test_list_blocks_filters_by_state(api_client: TestClient, migrated_db: Engine) -> None:
    raw_key, document_id, needs_id, _approved = _seed_review_fixture(migrated_db)
    headers = {"X-Api-Key": raw_key}

    all_blocks = api_client.get(f"/v1/documents/{document_id}/blocks", headers=headers)
    assert all_blocks.status_code == HTTPStatus.OK
    assert len(all_blocks.json()) == 2

    filtered = api_client.get(
        f"/v1/documents/{document_id}/blocks",
        params={"state": "needs_review"},
        headers=headers,
    )
    assert filtered.status_code == HTTPStatus.OK
    body = filtered.json()
    assert len(body) == 1
    assert body[0]["id"] == needs_id
    assert body[0]["review_state"] == "needs_review"


def test_claim_approve_flow(api_client: TestClient, migrated_db: Engine) -> None:
    raw_key, document_id, needs_id, approved_id = _seed_review_fixture(migrated_db)
    headers = {"X-Api-Key": raw_key}

    claimed = api_client.post(f"/v1/blocks/{needs_id}/claim", headers=headers)
    assert claimed.status_code == HTTPStatus.OK
    assert claimed.json()["review_state"] == "in_review"
    assert claimed.json()["version"] == 2

    approved = api_client.post(f"/v1/blocks/{needs_id}/approve", headers=headers)
    assert approved.status_code == HTTPStatus.OK
    assert approved.json()["review_state"] == "approved"

    # Cannot approve an already-approved block.
    bad = api_client.post(f"/v1/blocks/{approved_id}/approve", headers=headers)
    assert bad.status_code == HTTPStatus.CONFLICT

    finalized = api_client.post(f"/v1/documents/{document_id}/finalize", headers=headers)
    assert finalized.status_code == HTTPStatus.OK
    assert finalized.json()["status"] == "indexing"
    assert finalized.json()["needs_review_count"] == 0


def test_patch_requires_if_match_and_records_revision(
    api_client: TestClient, migrated_db: Engine
) -> None:
    raw_key, document_id, needs_id, _approved = _seed_review_fixture(migrated_db)
    headers = {"X-Api-Key": raw_key}

    claimed = api_client.post(f"/v1/blocks/{needs_id}/claim", headers=headers)
    assert claimed.status_code == HTTPStatus.OK
    version = claimed.json()["version"]

    missing = api_client.patch(
        f"/v1/blocks/{needs_id}",
        headers=headers,
        json={"text": "edited"},
    )
    assert missing.status_code == HTTPStatus.PRECONDITION_REQUIRED

    stale = api_client.patch(
        f"/v1/blocks/{needs_id}",
        headers={**headers, "If-Match": "1"},
        json={"text": "edited"},
    )
    assert stale.status_code == HTTPStatus.PRECONDITION_FAILED

    edited = api_client.patch(
        f"/v1/blocks/{needs_id}",
        headers={**headers, "If-Match": str(version)},
        json={"text": "edited copy"},
    )
    assert edited.status_code == HTTPStatus.OK
    assert edited.json()["review_state"] == "edited"
    assert edited.json()["text"] == "edited copy"
    assert edited.json()["version"] == version + 1

    # Still open (approved sibling + edited) — finalize should fail until approved sibling
    # only? edited is finalize-ready; needs was the open one. Both approved sibling and
    # edited are finalize-ready.
    finalized = api_client.post(f"/v1/documents/{document_id}/finalize", headers=headers)
    assert finalized.status_code == HTTPStatus.OK


def test_finalize_blocked_while_needs_review(api_client: TestClient, migrated_db: Engine) -> None:
    raw_key, document_id, _needs_id, _approved = _seed_review_fixture(migrated_db)
    headers = {"X-Api-Key": raw_key}
    response = api_client.post(f"/v1/documents/{document_id}/finalize", headers=headers)
    assert response.status_code == HTTPStatus.CONFLICT
