"""Phase 4 chat_sessions + chat_turns with RLS.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-12

DDL from ``02-data-model.md`` §4.16.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE chat_sessions (
          id              text PRIMARY KEY,
          tenant_id       text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          collection_id   text NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
          user_sub        text NOT NULL,
          title           text,
          rolling_summary text,
          long_term_facts jsonb NOT NULL DEFAULT '[]',
          created_at      timestamptz NOT NULL DEFAULT now(),
          last_message_at timestamptz,
          deleted_at      timestamptz
        )
        """
    )
    op.execute("CREATE INDEX chat_sessions_tenant_idx ON chat_sessions(tenant_id)")
    op.execute("CREATE INDEX chat_sessions_collection_idx ON chat_sessions(collection_id)")
    op.execute(
        """
        CREATE INDEX chat_sessions_user_idx
          ON chat_sessions(tenant_id, collection_id, user_sub)
          WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE chat_turns (
          id                text PRIMARY KEY,
          session_id        text NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
          role              text NOT NULL
                            CHECK (role IN ('user','assistant','tool','system')),
          content           text NOT NULL,
          cited_chunk_ids   text[] NOT NULL DEFAULT '{}',
          cited_documents   text[] NOT NULL DEFAULT '{}',
          usage             jsonb,
          latency_ms        int,
          langfuse_trace_id text,
          created_at        timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX chat_turns_session_idx ON chat_turns(session_id, created_at)")

    op.execute("ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chat_sessions FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY chat_sessions_tenant_isolation ON chat_sessions
          USING (tenant_id = current_setting('sift.tenant_id', true))
        """
    )

    op.execute("ALTER TABLE chat_turns ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chat_turns FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY chat_turns_tenant_isolation ON chat_turns
          USING (
            EXISTS (
              SELECT 1 FROM chat_sessions s
              WHERE s.id = chat_turns.session_id
                AND s.tenant_id = current_setting('sift.tenant_id', true)
            )
          )
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON chat_sessions TO sift_app, sift_admin")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON chat_turns TO sift_app, sift_admin")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS chat_turns_tenant_isolation ON chat_turns")
    op.execute("DROP TABLE IF EXISTS chat_turns")
    op.execute("DROP POLICY IF EXISTS chat_sessions_tenant_isolation ON chat_sessions")
    op.execute("DROP TABLE IF EXISTS chat_sessions")
