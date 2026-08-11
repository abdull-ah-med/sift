"""Phase 1 audit_events table + RLS (ADR-0014).

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-11

Hashing is performed in application code (``sift_core.audit.write_audit_event``).
This migration creates storage, uniqueness, and tenant RLS only.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE audit_events (
          event_id     text PRIMARY KEY,
          tenant_id    text NOT NULL,
          chain_index  bigint NOT NULL,
          occurred_at  timestamptz(6) NOT NULL,
          actor        text NOT NULL,
          action       text NOT NULL,
          target_kind  text NOT NULL,
          target_id    text NOT NULL DEFAULT '',
          payload      jsonb NOT NULL,
          request_id   text,
          ip_hash      text,
          prev_hash    bytea NOT NULL,
          event_hash   bytea NOT NULL,
          created_at   timestamptz NOT NULL DEFAULT now(),
          CHECK (octet_length(prev_hash) = 32),
          CHECK (octet_length(event_hash) = 32)
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX audit_events_chain_uq ON audit_events (tenant_id, chain_index)")
    op.execute(
        """
        CREATE INDEX audit_events_tenant_time_idx
          ON audit_events (tenant_id, occurred_at DESC)
        """
    )

    op.execute("ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_events FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY audit_events_tenant_isolation ON audit_events
          USING (tenant_id = current_setting('sift.tenant_id', true))
        """
    )
    # Application writes via write_audit_event under sift_app; ad-hoc inserts
    # outside that helper are still gated by RLS + app discipline (ADR-0014).
    op.execute("GRANT SELECT, INSERT ON audit_events TO sift_app, sift_admin")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS audit_events_tenant_isolation ON audit_events")
    op.execute("DROP TABLE IF EXISTS audit_events")
