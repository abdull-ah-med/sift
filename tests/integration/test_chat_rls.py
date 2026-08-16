"""RLS isolation for chat_sessions / chat_turns (requires Postgres)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.engine import Engine

from sift_core.db import tenant_guc_statements
from sift_core.ids import IdKind, new_id

pytestmark = pytest.mark.integration


def _apply_tenant_context(connection: Connection, tenant_id: str) -> None:
    for statement in tenant_guc_statements(tenant_id):
        connection.execute(text(statement))


def test_chat_rls_tenant_a_cannot_read_tenant_b_sessions(migrated_db: Engine) -> None:
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_a = new_id(IdKind.TENANT)
    tenant_b = new_id(IdKind.TENANT)
    col_a = new_id(IdKind.COLLECTION)
    col_b = new_id(IdKind.COLLECTION)
    sess_a = f"sess_{new_id(IdKind.SESSION).split('_', 1)[-1]}"
    sess_b = f"sess_{new_id(IdKind.SESSION).split('_', 1)[-1]}"
    turn_b = f"turn_{new_id(IdKind.SESSION).split('_', 1)[-1]}"
    now = datetime.now(UTC)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("INSERT INTO organizations (id, name, slug, created_at) VALUES (:id,'O',:s,:n)"),
            {"id": org_id, "s": f"o-{org_id[-8:].lower()}", "n": now},
        )
        for tid, slug in ((tenant_a, "ta"), (tenant_b, "tb")):
            conn.execute(
                text(
                    "INSERT INTO tenants (id, organization_id, name, slug, created_at) "
                    "VALUES (:id,:org,:name,:slug,:n)"
                ),
                {
                    "id": tid,
                    "org": org_id,
                    "name": slug,
                    "slug": f"{slug}-{tid[-6:].lower()}",
                    "n": now,
                },
            )
        for cid, tid, slug in ((col_a, tenant_a, "ca"), (col_b, tenant_b, "cb")):
            conn.execute(
                text(
                    "INSERT INTO collections (id, tenant_id, name, slug, created_at) "
                    "VALUES (:id,:tid,:name,:slug,:n)"
                ),
                {
                    "id": cid,
                    "tid": tid,
                    "name": slug,
                    "slug": f"{slug}-{cid[-6:].lower()}",
                    "n": now,
                },
            )
        for sid, tid, cid in ((sess_a, tenant_a, col_a), (sess_b, tenant_b, col_b)):
            conn.execute(
                text(
                    """
                    INSERT INTO chat_sessions (
                      id, tenant_id, collection_id, user_sub, title, created_at
                    ) VALUES (:id, :tid, :cid, 'user-a', 't', :n)
                    """
                ),
                {"id": sid, "tid": tid, "cid": cid, "n": now},
            )
        conn.execute(
            text(
                """
                INSERT INTO chat_turns (
                  id, session_id, role, content, cited_chunk_ids, cited_documents, created_at
                ) VALUES (
                  :id, :sid, 'assistant', 'secret-b', ARRAY[]::text[], ARRAY[]::text[], :n
                )
                """
            ),
            {"id": turn_b, "sid": sess_b, "n": now},
        )

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_app"))
        _apply_tenant_context(conn, tenant_a)
        sessions = conn.execute(text("SELECT id FROM chat_sessions")).fetchall()
        turns = conn.execute(text("SELECT id FROM chat_turns")).fetchall()
        assert {r[0] for r in sessions} == {sess_a}
        assert turns == []
