"""Register enqueues Taskiq only; worker is sole parse path (Phase 2 p2re-5)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine

from sift_api import db as db_mod
from sift_api.main import app
from sift_api.settings import get_settings
from sift_api.tasks import ingest_document
from sift_core.auth.api_keys import mint_api_key
from sift_core.ids import IdKind, new_id

PEPPER = "phase2-register-enqueue-pepper-do-not-use-prod"
CORPUS = Path(__file__).resolve().parents[2] / "evals" / "corpus"
DIGITAL_PDF = sorted(CORPUS.glob("digital-*.pdf"))[0]


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


def _seed_collection(engine: Engine) -> tuple[str, str, str]:
    """Return (tenant_id, collection_id, write_raw_key)."""
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    collection_id = new_id(IdKind.COLLECTION)
    write_key = mint_api_key(PEPPER.encode())
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text(
                "INSERT INTO organizations (id, name, slug, created_at) "
                "VALUES (:id, 'R', :slug, :now)"
            ),
            {"id": org_id, "slug": f"o-{org_id[-8:].lower()}", "now": now},
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
                "hash": write_key.hash,
                "prefix": write_key.prefix,
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
    return tenant_id, collection_id, write_key.raw


@pytest.mark.integration
def test_register_enqueues_taskiq_without_sync_ingest(
    api_client: TestClient,
    migrated_db: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant_id, collection_id, write_raw = _seed_collection(migrated_db)
    doc_id = new_id(IdKind.DOCUMENT)
    object_key = f"t/{tenant_id}/d/{doc_id}/original.pdf"

    sync_calls: list[dict[str, Any]] = []

    def _sync_spy(**kwargs: Any) -> str:
        sync_calls.append(kwargs)
        return "indexing"

    monkeypatch.setattr("sift_api.ingest.run_ingest_document", _sync_spy)
    monkeypatch.setattr("sift_api.routes.v1.run_ingest_document", _sync_spy, raising=False)

    kiq_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    async def _fake_kiq(*args: Any, **kwargs: Any) -> object:
        kiq_calls.append((args, kwargs))
        return object()

    monkeypatch.setattr(ingest_document, "kiq", _fake_kiq)

    response = api_client.post(
        f"/v1/collections/{collection_id}/documents",
        headers={"X-Api-Key": write_raw},
        json={
            "object_key": object_key,
            "title": "Queued Doc",
            "slug": f"q-{doc_id[-8:].lower()}",
            "source_mime": "application/pdf",
            "source_bytes": 12,
            "source_sha256": "a" * 64,
        },
    )
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["id"] == doc_id
    assert body["status"] == "queued"
    assert sync_calls == [], "API register must not call run_ingest_document"
    assert len(kiq_calls) == 1
    args, _kwargs = kiq_calls[0]
    assert args[0] == doc_id
    assert args[2] == tenant_id
    job_id = args[1]
    assert job_id.startswith("job_")

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        doc_status = conn.execute(
            text("SELECT status FROM documents WHERE id = :id"),
            {"id": doc_id},
        ).scalar_one()
        job_status = conn.execute(
            text("SELECT status FROM jobs WHERE id = :id"),
            {"id": job_id},
        ).scalar_one()
    assert doc_status == "queued"
    assert job_status == "queued"


@pytest.mark.integration
def test_register_returns_503_when_enqueue_fails(
    api_client: TestClient,
    migrated_db: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tenant_id, collection_id, write_raw = _seed_collection(migrated_db)
    doc_id = new_id(IdKind.DOCUMENT)
    object_key = f"t/{tenant_id}/d/{doc_id}/original.pdf"

    monkeypatch.setattr(
        "sift_api.ingest.run_ingest_document",
        lambda **_k: (_ for _ in ()).throw(AssertionError("sync ingest forbidden")),
    )
    monkeypatch.setattr(
        "sift_api.routes.v1.run_ingest_document",
        lambda **_k: (_ for _ in ()).throw(AssertionError("sync ingest forbidden")),
        raising=False,
    )

    async def _fail_kiq(*_a: Any, **_k: Any) -> object:
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(ingest_document, "kiq", _fail_kiq)

    response = api_client.post(
        f"/v1/collections/{collection_id}/documents",
        headers={"X-Api-Key": write_raw},
        json={
            "object_key": object_key,
            "title": "No Broker",
            "slug": f"n-{doc_id[-8:].lower()}",
            "source_mime": "application/pdf",
            "source_bytes": 12,
            "source_sha256": "b" * 64,
        },
    )
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


@pytest.mark.integration
@pytest.mark.asyncio
async def test_worker_task_is_sole_parse_entrypoint(
    migrated_db: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Worker task (original_func) runs parse; same path Taskiq worker executes."""
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

    def _fake_download(*, source_uri: str, dest: Path, settings: object) -> None:
        del source_uri, settings
        dest.write_bytes(DIGITAL_PDF.read_bytes())

    monkeypatch.setattr("sift_api.ingest.download_object", _fake_download)
    monkeypatch.setenv("SIFT_PARSE_ENGINE", "digital-only")

    await ingest_document.original_func(document_id, job_id, tenant_id)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        status = conn.execute(
            text("SELECT status FROM documents WHERE id = :id"),
            {"id": document_id},
        ).scalar_one()
        block_count = conn.execute(
            text("SELECT count(*) FROM blocks WHERE document_id = :id"),
            {"id": document_id},
        ).scalar_one()
    assert status == "indexing"
    assert int(block_count) > 0
