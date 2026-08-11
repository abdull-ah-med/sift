"""Integration tests for audit hash-chain write + verify (ADR-0014)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine

from sift_core.audit import verify_chain, write_audit_event
from sift_core.db import tenant_guc_statements
from sift_core.ids import IdKind, new_id


def _apply_tenant(connection, tenant_id: str) -> None:
    for statement in tenant_guc_statements(tenant_id):
        connection.execute(text(statement))


def test_write_audit_event_when_chained_verifies_clean(migrated_db: Engine) -> None:
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'Acme', 'acme')"),
            {"id": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug)
                VALUES (:id, :org, 'Tenant A', 'tenant-a')
                """
            ),
            {"id": tenant_id, "org": org_id},
        )

        first = write_audit_event(
            conn,
            tenant_id=tenant_id,
            actor="system",
            action="tenant.create",
            target_kind="tenant",
            target_id=tenant_id,
            payload={"tenant_name": "Tenant A", "created_by": "user:sub-1"},
            occurred_at=datetime(2026, 8, 11, 14, 0, 0, 0, tzinfo=UTC),
        )
        second = write_audit_event(
            conn,
            tenant_id=tenant_id,
            actor="user:sub-1",
            action="document.upload",
            target_kind="document",
            target_id=new_id(IdKind.DOCUMENT),
            payload={"bytes": 10},
            request_id="req-1",
            occurred_at=datetime(2026, 8, 11, 14, 0, 1, 0, tzinfo=UTC),
        )

        assert first.chain_index == 1
        assert second.chain_index == first.chain_index + 1
        assert second.prev_hash == first.event_hash

        report = verify_chain(conn, tenant_id)
        assert report.ok is True
        assert report.checked == second.chain_index


def test_verify_chain_when_payload_tampered_reports_index(migrated_db: Engine) -> None:
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'Acme', 'acme2')"),
            {"id": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug)
                VALUES (:id, :org, 'Tenant B', 'tenant-b')
                """
            ),
            {"id": tenant_id, "org": org_id},
        )
        write_audit_event(
            conn,
            tenant_id=tenant_id,
            actor="system",
            action="tenant.create",
            target_kind="tenant",
            target_id=tenant_id,
            payload={"tenant_name": "Tenant B"},
            occurred_at=datetime(2026, 8, 11, 15, 0, 0, 0, tzinfo=UTC),
        )
        conn.execute(text("RESET ROLE"))
        conn.execute(
            text(
                """
                UPDATE audit_events
                SET payload = '{"tenant_name":"EVIL"}'::jsonb
                WHERE tenant_id = :tenant_id AND chain_index = 1
                """
            ),
            {"tenant_id": tenant_id},
        )
        report = verify_chain(conn, tenant_id)

    assert report.ok is False
    assert report.tampered_at_index == 1


def test_rls_when_tenant_a_cannot_read_tenant_b_audit_events(migrated_db: Engine) -> None:
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_a = new_id(IdKind.TENANT)
    tenant_b = new_id(IdKind.TENANT)

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text("INSERT INTO organizations (id, name, slug) VALUES (:id, 'Acme', 'acme3')"),
            {"id": org_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug) VALUES
                  (:a, :org, 'A', 'a'),
                  (:b, :org, 'B', 'b')
                """
            ),
            {"a": tenant_a, "b": tenant_b, "org": org_id},
        )
        write_audit_event(
            conn,
            tenant_id=tenant_a,
            actor="system",
            action="tenant.create",
            target_kind="tenant",
            target_id=tenant_a,
            payload={},
        )
        write_audit_event(
            conn,
            tenant_id=tenant_b,
            actor="system",
            action="tenant.create",
            target_kind="tenant",
            target_id=tenant_b,
            payload={},
        )

    with migrated_db.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_app"))
        _apply_tenant(conn, tenant_a)
        visible = conn.execute(text("SELECT tenant_id FROM audit_events")).scalars().all()

    assert visible == [tenant_a]
