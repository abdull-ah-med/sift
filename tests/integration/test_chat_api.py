"""Integration: chat session auth matrix + CRUD smoke (requires Postgres)."""

from __future__ import annotations

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

PEPPER = "phase4-chat-test-pepper"
pytestmark = pytest.mark.integration


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


def _seed(engine: Engine) -> tuple[str, str, str, str]:
    """Return tenant_id, collection_id, chat_raw_key, search_raw_key."""
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    collection_id = new_id(IdKind.COLLECTION)
    chat_key = mint_api_key(PEPPER.encode())
    search_key = mint_api_key(PEPPER.encode())
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
        for name, minted, scopes in (
            ("chat", chat_key, ["chat"]),
            ("search", search_key, ["search"]),
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
    return tenant_id, collection_id, chat_key.raw, search_key.raw


def test_chat_sessions_unauthenticated_returns_401(
    api_client: TestClient, migrated_db: Engine
) -> None:
    _t, collection_id, _c, _s = _seed(migrated_db)
    response = api_client.get(f"/v1/collections/{collection_id}/chat/sessions")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_chat_sessions_wrong_scope_returns_403(
    api_client: TestClient, migrated_db: Engine
) -> None:
    _t, collection_id, _chat, search_raw = _seed(migrated_db)
    response = api_client.get(
        f"/v1/collections/{collection_id}/chat/sessions",
        headers={"X-Api-Key": search_raw},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_chat_session_create_list_delete_happy(
    api_client: TestClient, migrated_db: Engine
) -> None:
    _t, collection_id, chat_raw, _s = _seed(migrated_db)
    created = api_client.post(
        f"/v1/collections/{collection_id}/chat/sessions",
        headers={"X-Api-Key": chat_raw},
        json={"title": "Refund Qs"},
    )
    assert created.status_code in (HTTPStatus.OK, HTTPStatus.CREATED)
    session_id = created.json()["id"]
    assert session_id.startswith("sess_") or session_id

    listed = api_client.get(
        f"/v1/collections/{collection_id}/chat/sessions",
        headers={"X-Api-Key": chat_raw},
    )
    assert listed.status_code == HTTPStatus.OK
    assert any(row["id"] == session_id for row in listed.json())

    detail = api_client.get(
        f"/v1/chat/sessions/{session_id}",
        headers={"X-Api-Key": chat_raw},
    )
    assert detail.status_code == HTTPStatus.OK
    assert detail.json()["title"] == "Refund Qs"

    deleted = api_client.delete(
        f"/v1/chat/sessions/{session_id}",
        headers={"X-Api-Key": chat_raw},
    )
    assert deleted.status_code in (HTTPStatus.OK, HTTPStatus.NO_CONTENT)
