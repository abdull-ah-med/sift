"""Phase 2 chunks table (unembedded; BM25 index deferred to Phase 3).

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-11

DDL from ``02-data-model.md`` §4.9 minus ParadeDB BM25 (Phase 3 retrieval).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE chunks (
          id                  text PRIMARY KEY,
          tenant_id           text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          document_id         text NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
          collection_id       text NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
          ordinal             int NOT NULL,
          text_raw            text NOT NULL,
          text_contextualized text NOT NULL,
          token_count         int NOT NULL,
          chunk_type          text NOT NULL,
          section_path        text[] NOT NULL DEFAULT '{}',
          page_numbers        int[] NOT NULL DEFAULT '{}',
          block_ids           text[] NOT NULL DEFAULT '{}',
          quality_score       float,
          bm25_language       text NOT NULL DEFAULT 'english',
          review_state        text NOT NULL DEFAULT 'approved'
                              CHECK (review_state IN ('approved','edited','rejected')),
          metadata            jsonb NOT NULL DEFAULT '{}',
          created_at          timestamptz NOT NULL DEFAULT now(),
          UNIQUE (document_id, ordinal)
        )
        """
    )
    op.execute("CREATE INDEX chunks_collection_idx ON chunks(collection_id)")
    op.execute("CREATE INDEX chunks_document_idx ON chunks(document_id)")
    op.execute("CREATE INDEX chunks_tenant_idx ON chunks(tenant_id)")

    op.execute("ALTER TABLE chunks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chunks FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY chunks_tenant_isolation ON chunks
          USING (tenant_id = current_setting('sift.tenant_id', true))
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON chunks TO sift_app, sift_admin")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS chunks_tenant_isolation ON chunks")
    op.execute("DROP TABLE IF EXISTS chunks")
