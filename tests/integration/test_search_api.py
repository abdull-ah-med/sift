"""Integration: POST /v1/collections/{id}/search auth matrix + happy path."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

from sift_api import db as db_mod
from sift_api.embed import EMBED_DIM, run_embed_document
from sift_api.main import app
from sift_api.search import query_hash
from sift_api.settings import get_settings
from sift_core.auth.api_keys import mint_api_key
from sift_core.ids import IdKind, new_id

PEPPER = "phase3-search-test-pepper"
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


def _seed(engine: Engine) -> tuple[str, str, str, str, str, str]:
    """Return tenant_id, collection_id, doc_id, chunk_id, search_key, read_key."""
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    collection_id = new_id(IdKind.COLLECTION)
    doc_id = new_id(IdKind.DOCUMENT)
    chunk_id = new_id(IdKind.CHUNK)
    search_key = mint_api_key(PEPPER.encode())
    read_key = mint_api_key(PEPPER.encode())
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
                  status, tags, created_by, created_at
                ) VALUES (
                  :id, :tid, :cid, 'EU T&Cs 2026', :slug, 's://x', 'application/pdf', 1, :sha,
                  'indexing', ARRAY['policy'], 'u', :n
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
                  text_raw, text_contextualized, token_count, chunk_type,
                  section_path, page_numbers, block_ids, review_state
                ) VALUES (
                  :id, :tid, :did, :cid, 0, 'refund policy text',
                  'refund policy for EU customers', 4, 'text',
                  ARRAY['Refunds','EU'], ARRAY[12,13], ARRAY['blk_a'], 'approved'
                )
                """
            ),
            {"id": chunk_id, "tid": tenant_id, "did": doc_id, "cid": collection_id},
        )
        for name, minted, scopes in (
            ("search", search_key, ["search"]),
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
    tei = MagicMock()
    tei.embed.return_value = [[0.04] * EMBED_DIM]
    run_embed_document(document_id=doc_id, tenant_id=tenant_id, tei=tei, engine=engine)
    return tenant_id, collection_id, doc_id, chunk_id, search_key.raw, read_key.raw


def test_search_unauthenticated_returns_401(api_client: TestClient, migrated_db: Engine) -> None:
    _t, collection_id, *_rest = _seed(migrated_db)
    response = api_client.post(
        f"/v1/collections/{collection_id}/search",
        json={"query": "refund"},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_search_wrong_scope_returns_403(api_client: TestClient, migrated_db: Engine) -> None:
    _t, collection_id, _d, _c, _search, read_raw = _seed(migrated_db)
    response = api_client.post(
        f"/v1/collections/{collection_id}/search",
        headers={"X-Api-Key": read_raw},
        json={"query": "refund"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_search_missing_collection_returns_404(api_client: TestClient, migrated_db: Engine) -> None:
    _t, _cid, _d, _c, search_raw, _read = _seed(migrated_db)
    foreign = new_id(IdKind.COLLECTION)
    response = api_client.post(
        f"/v1/collections/{foreign}/search",
        headers={"X-Api-Key": search_raw},
        json={"query": "refund"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_search_happy_path_returns_citations_and_audits_hash(
    api_client: TestClient, migrated_db: Engine
) -> None:
    tenant_id, collection_id, doc_id, chunk_id, search_raw, _read = _seed(migrated_db)
    query = "refund policy for EU"

    with (
        patch("sift_api.search.TeiClient") as tei_cls,
        patch("sift_api.search.TeiReranker") as rerank_cls,
    ):
        tei = tei_cls.return_value
        tei.embed.return_value = [[0.04] * EMBED_DIM]
        rerank = rerank_cls.return_value
        rerank.rerank.return_value = [(chunk_id, 0.94)]

        response = api_client.post(
            f"/v1/collections/{collection_id}/search",
            headers={"X-Api-Key": search_raw},
            json={
                "query": query,
                "top_k": 5,
                "include_text": True,
                "include_provenance": True,
                "rerank": True,
            },
        )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["results"]
    hit = body["results"][0]
    assert hit["chunk_id"] == chunk_id
    assert hit["document_id"] == doc_id
    assert hit["document_title"] == "EU T&Cs 2026"
    assert "refund" in (hit.get("text") or "").lower()
    assert hit["section_path"] == ["Refunds", "EU"]
    assert hit["page_numbers"] == [12, 13]
    assert "trace_id" in body

    with migrated_db.connect() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        row = (
            conn.execute(
                text(
                    """
                    SELECT action, payload FROM audit_events
                    WHERE tenant_id = :tid AND action = 'search.query'
                    ORDER BY created_at DESC LIMIT 1
                    """
                ),
                {"tid": tenant_id},
            )
            .mappings()
            .one()
        )
    payload = row["payload"]
    assert payload["query_hash"] == query_hash(query)
    assert "query" not in payload
    assert query not in str(payload)
