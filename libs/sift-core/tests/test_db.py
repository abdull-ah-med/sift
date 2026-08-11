"""Unit tests for tenant GUC helpers."""

from sift_core.db import tenant_guc_statements


def test_tenant_guc_statements_when_tenant_only() -> None:
    stmts = tenant_guc_statements("tenant_01HABCDEFGHJKMNPQRSTVWXYZ")

    assert len(stmts) == 1
    assert "sift.tenant_id" in stmts[0]
    assert "tenant_01HABCDEFGHJKMNPQRSTVWXYZ" in stmts[0]
    assert ", true)" in stmts[0]


def test_tenant_guc_statements_when_principals_escapes_quotes() -> None:
    stmts = tenant_guc_statements("tenant_01HABCDEFGHJKMNPQRSTVWXYZ", principals=["user_a", 'x"y'])

    assert "sift.tenant_id" in stmts[0]
    assert "sift.principals" in stmts[1]
    assert 'x\\"y' in stmts[1]
    assert stmts[0] != stmts[1]
