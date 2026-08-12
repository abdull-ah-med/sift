"""Phase 3 chunk_embeddings (pgvector dense + sparse) with RLS.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-12

DDL from ``02-data-model.md`` §4.10.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE chunk_embeddings (
          chunk_id      text PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
          tenant_id     text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          collection_id text NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
          model         text NOT NULL,
          dim           int NOT NULL,
          embedding     vector(1024) NOT NULL,
          sparse        jsonb
        )
        """
    )
    op.execute(
        """
        CREATE INDEX chunk_embeddings_vec_idx
          ON chunk_embeddings USING hnsw (embedding vector_cosine_ops)
        """
    )
    op.execute("CREATE INDEX chunk_embeddings_collection_idx ON chunk_embeddings(collection_id)")
    op.execute("CREATE INDEX chunk_embeddings_tenant_idx ON chunk_embeddings(tenant_id)")

    op.execute("ALTER TABLE chunk_embeddings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chunk_embeddings FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY chunk_embeddings_tenant_isolation ON chunk_embeddings
          USING (tenant_id = current_setting('sift.tenant_id', true))
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON chunk_embeddings TO sift_app, sift_admin")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS chunk_embeddings_tenant_isolation ON chunk_embeddings")
    op.execute("DROP TABLE IF EXISTS chunk_embeddings")
