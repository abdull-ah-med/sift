"""Phase 3 ParadeDB BM25 index on chunks.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-12

DDL from ``02-data-model.md`` §4.9 BM25 (deferred from Phase 2).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ParadeDB pg_search; USING bm25 remains a supported alias for USING paradedb.
    op.execute(
        """
        CREATE INDEX chunks_bm25_idx ON chunks
        USING bm25 (id, text_contextualized, tenant_id, collection_id)
        WITH (
          key_field='id',
          text_fields='{"text_contextualized":{"tokenizer":{"type":"default"}}}'
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS chunks_bm25_idx")
