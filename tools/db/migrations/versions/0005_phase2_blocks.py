"""Phase 2 blocks + block_revisions tables with RLS.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-11

DDL from ``02-data-model.md`` sections 4.7-4.8 plus Phase 2 plan additions:
- ``blocks.version`` for optimistic concurrency (If-Match)
- ``block_revisions.tenant_id`` so RLS matches other tenant-scoped tables
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE blocks (
          id                 text PRIMARY KEY,
          tenant_id          text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          document_id        text NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
          ordinal            int NOT NULL,
          block_type         text NOT NULL,
          text               text,
          html               text,
          provenance         jsonb NOT NULL,
          confidence         float,
          hierarchy          jsonb,
          cross_refs         text[] NOT NULL DEFAULT '{}',
          table_data         jsonb,
          figure_data        jsonb,
          formula_data       jsonb,
          pii_map            jsonb,
          review_state       text NOT NULL DEFAULT 'pending'
                             CHECK (review_state IN (
                               'pending','needs_review','in_review',
                               'approved','edited','rejected','conflict'
                             )),
          latest_revision_id text,
          version            int NOT NULL DEFAULT 1,
          created_at         timestamptz NOT NULL DEFAULT now(),
          UNIQUE (document_id, ordinal)
        )
        """
    )
    op.execute("CREATE INDEX blocks_tenant_idx ON blocks(tenant_id)")
    op.execute("CREATE INDEX blocks_document_idx ON blocks(document_id)")
    op.execute(
        """
        CREATE INDEX blocks_needs_review_idx ON blocks(document_id)
          WHERE review_state IN ('needs_review','in_review')
        """
    )

    op.execute(
        """
        CREATE TABLE block_revisions (
          id           text PRIMARY KEY,
          tenant_id    text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          block_id     text NOT NULL REFERENCES blocks(id) ON DELETE CASCADE,
          text_before  text,
          text_after   text,
          diff_summary text,
          action       text NOT NULL
                       CHECK (action IN ('edit','approve','reject','purge')),
          actor_sub    text NOT NULL,
          reason       text,
          created_at   timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX block_revisions_block_idx ON block_revisions(block_id)")
    op.execute("CREATE INDEX block_revisions_tenant_idx ON block_revisions(tenant_id)")

    for table in ("blocks", "block_revisions"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
              USING (tenant_id = current_setting('sift.tenant_id', true))
            """
        )
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO sift_app, sift_admin")


def downgrade() -> None:
    for table in ("block_revisions", "blocks"):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"DROP TABLE IF EXISTS {table}")
