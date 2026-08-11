"""Migration + RLS isolation tests (requires Postgres).

Skipped unless Postgres is reachable (see ``conftest.py``). Start with
``docker compose -f deploy/compose/dev.yml up -d postgres``.
"""

from __future__ import annotations

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, text
from sqlalchemy.engine import Engine

from sift_core.db import tenant_guc_statements
from sift_core.ids import IdKind, new_id

TENANCY_TABLES = frozenset({"organizations", "tenants", "users_in_tenant"})
CORPUS_TABLES = frozenset({"api_keys", "collections", "documents", "jobs"})
AUDIT_TABLES = frozenset({"audit_events"})
PHASE1_TABLES = TENANCY_TABLES | CORPUS_TABLES | AUDIT_TABLES


def _apply_tenant_context(connection: Connection, tenant_id: str) -> None:
    for statement in tenant_guc_statements(tenant_id):
        connection.execute(text(statement))


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


def test_alembic_upgrade_downgrade_upgrade_when_postgres_available(
    alembic_cfg: Config,
    pg_engine: Engine,
) -> None:
    command.upgrade(alembic_cfg, "head")
    with pg_engine.connect() as conn:
        assert _public_tables(conn, PHASE1_TABLES) == set(PHASE1_TABLES)

    command.downgrade(alembic_cfg, "-1")
    with pg_engine.connect() as conn:
        assert _public_tables(conn, AUDIT_TABLES) == set()
        assert _public_tables(conn, CORPUS_TABLES) == set(CORPUS_TABLES)

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
