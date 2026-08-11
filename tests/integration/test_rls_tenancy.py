"""Migration + RLS isolation tests (requires Postgres).

Skipped unless Postgres is reachable at SIFT_PG_DSN / DATABASE_URL / default
local Compose DSN. Start stack with ``make up`` (postgres service).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import Engine

from sift_core.db import tenant_guc_statements
from sift_core.ids import IdKind, new_id

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "tools" / "db" / "alembic.ini"

TENANCY_TABLES = frozenset({"organizations", "tenants", "users_in_tenant"})
CORPUS_TABLES = frozenset({"api_keys", "collections", "documents", "jobs"})
PHASE1_TABLES = TENANCY_TABLES | CORPUS_TABLES


def _apply_tenant_context(connection: Connection, tenant_id: str) -> None:
    for statement in tenant_guc_statements(tenant_id):
        connection.execute(text(statement))


def _sync_dsn() -> str:
    raw = os.environ.get("SIFT_PG_DSN") or os.environ.get("DATABASE_URL")
    if not raw:
        raw = "postgresql+psycopg://sift:sift@127.0.0.1:5432/sift"
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql+asyncpg://")
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql://")
    return raw


def _postgres_reachable(dsn: str) -> bool:
    engine = create_engine(dsn, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        engine.dispose()


def _public_tables(conn: Connection, names: frozenset[str]) -> set[str]:
    rows = conn.execute(
        text(
            """
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public' AND tablename = ANY(:names)
            """
        ),
        {"names": list(names)},
    )
    return {row[0] for row in rows}


@pytest.fixture(scope="module")
def pg_dsn() -> str:
    dsn = _sync_dsn()
    if not _postgres_reachable(dsn):
        pytest.skip("Postgres not reachable; start deploy/compose/dev.yml postgres")
    return dsn


@pytest.fixture(scope="module")
def pg_engine(pg_dsn: str) -> Iterator[Engine]:
    engine = create_engine(pg_dsn, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def alembic_cfg(pg_dsn: str) -> Iterator[Config]:
    # Never use str(engine.url) — SQLAlchemy hides the password as ***.
    previous = os.environ.get("SIFT_PG_DSN")
    os.environ["SIFT_PG_DSN"] = pg_dsn
    cfg = Config(str(ALEMBIC_INI))
    try:
        yield cfg
    finally:
        if previous is None:
            os.environ.pop("SIFT_PG_DSN", None)
        else:
            os.environ["SIFT_PG_DSN"] = previous


@pytest.fixture(scope="module")
def migrated_db(alembic_cfg: Config, pg_engine: Engine) -> Iterator[Engine]:
    command.upgrade(alembic_cfg, "head")
    yield pg_engine
    command.downgrade(alembic_cfg, "base")


def test_alembic_upgrade_downgrade_upgrade_when_postgres_available(
    alembic_cfg: Config,
    pg_engine: Engine,
) -> None:
    command.upgrade(alembic_cfg, "head")
    with pg_engine.connect() as conn:
        assert _public_tables(conn, PHASE1_TABLES) == set(PHASE1_TABLES)

    command.downgrade(alembic_cfg, "-1")
    with pg_engine.connect() as conn:
        assert _public_tables(conn, CORPUS_TABLES) == set()
        assert _public_tables(conn, TENANCY_TABLES) == set(TENANCY_TABLES)

    command.downgrade(alembic_cfg, "base")
    with pg_engine.connect() as conn:
        assert _public_tables(conn, PHASE1_TABLES) == set()

    command.upgrade(alembic_cfg, "head")
    with pg_engine.connect() as conn:
        assert _public_tables(conn, PHASE1_TABLES) == set(PHASE1_TABLES)


def test_rls_when_tenant_a_cannot_read_tenant_b_rows(migrated_db: Engine) -> None:
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_a = new_id(IdKind.TENANT)
    tenant_b = new_id(IdKind.TENANT)
    col_a = new_id(IdKind.COLLECTION)
    col_b = new_id(IdKind.COLLECTION)
    doc_a = new_id(IdKind.DOCUMENT)
    doc_b = new_id(IdKind.DOCUMENT)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text(
                """
                INSERT INTO organizations (id, name, slug)
                VALUES (:id, 'Acme', 'acme')
                """
            ),
            {"id": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug)
                VALUES
                  (:a, :org, 'Tenant A', 'tenant-a'),
                  (:b, :org, 'Tenant B', 'tenant-b')
                """
            ),
            {"a": tenant_a, "b": tenant_b, "org": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO users_in_tenant (tenant_id, user_sub, email, role)
                VALUES
                  (:a, 'user-a', 'a@example.com', 'owner'),
                  (:b, 'user-b', 'b@example.com', 'owner')
                """
            ),
            {"a": tenant_a, "b": tenant_b},
        )
        conn.execute(
            text(
                """
                INSERT INTO collections (id, tenant_id, name, slug)
                VALUES
                  (:ca, :a, 'Corpus A', 'corpus-a'),
                  (:cb, :b, 'Corpus B', 'corpus-b')
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
                  (
                    :da, :a, :ca, 'Doc A', 'doc-a',
                    'seaweed://t/a/d/a/original.pdf', 'application/pdf', 10, 'aaa',
                    'queued', 'user-a'
                  ),
                  (
                    :db, :b, :cb, 'Doc B', 'doc-b',
                    'seaweed://t/b/d/b/original.pdf', 'application/pdf', 10, 'bbb',
                    'queued', 'user-b'
                  )
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

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_app"))
        _apply_tenant_context(conn, tenant_a)
        visible_tenants = conn.execute(text("SELECT id FROM tenants ORDER BY slug")).scalars().all()
        visible_users = (
            conn.execute(text("SELECT user_sub FROM users_in_tenant ORDER BY user_sub"))
            .scalars()
            .all()
        )
        visible_collections = (
            conn.execute(text("SELECT id FROM collections ORDER BY slug")).scalars().all()
        )
        visible_documents = (
            conn.execute(text("SELECT id FROM documents ORDER BY slug")).scalars().all()
        )

    assert visible_tenants == [tenant_a]
    assert visible_users == ["user-a"]
    assert visible_collections == [col_a]
    assert visible_documents == [doc_a]
