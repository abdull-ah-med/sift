"""API key scope enforcement against live Postgres (Phase 1 exit criterion)."""

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

PEPPER = "phase1-test-pepper-do-not-use-prod"


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


def _seed_keys(engine: Engine) -> tuple[str, str, str]:
    """Return (tenant_id, write_raw_key, search_raw_key)."""
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    write_key = mint_api_key(PEPPER.encode())
    search_key = mint_api_key(PEPPER.encode())
    now = datetime.now(UTC)
    slug = f"t-{tenant_id[-8:].lower()}"
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text(
                "INSERT INTO organizations (id, name, slug, created_at) "
                "VALUES (:id, 'T', :slug, :now)"
            ),
            {"id": org_id, "slug": slug, "now": now},
        )
        conn.execute(
            text(
                "INSERT INTO tenants (id, organization_id, name, slug, created_at) "
                "VALUES (:id, :org, 'T', :slug, :now)"
            ),
            {"id": tenant_id, "org": org_id, "slug": slug, "now": now},
        )
        for name, minted, scopes in (
            ("write", write_key, ["documents:read", "documents:write"]),
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
    return tenant_id, write_key.raw, search_key.raw


def test_search_scoped_key_cannot_create_collection(
    api_client: TestClient,
    migrated_db: Engine,
) -> None:
    _tenant, write_raw, search_raw = _seed_keys(migrated_db)

    denied = api_client.post(
        "/v1/collections",
        headers={"X-Api-Key": search_raw},
        json={"name": "Nope", "slug": "nope"},
    )
    assert denied.status_code == HTTPStatus.FORBIDDEN

    allowed = api_client.post(
        "/v1/collections",
        headers={"X-Api-Key": write_raw},
        json={"name": "Yes", "slug": "yes"},
    )
    assert allowed.status_code == HTTPStatus.OK
    assert allowed.json()["slug"] == "yes"

    who = api_client.get("/v1/whoami", headers={"X-Api-Key": write_raw})
    assert who.status_code == HTTPStatus.OK
    assert "documents:write" in who.json()["scopes"]
