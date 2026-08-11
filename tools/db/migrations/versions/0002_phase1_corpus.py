"""Phase 1 corpus tables: api_keys, collections, documents, jobs + RLS.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-11

DDL from ``02-data-model.md`` sections 4.4-4.6 and 4.14. Tenant isolation RLS only;
document ACL via ``sift.principals`` is Phase 6 (spine section 3.4).

``audit_events`` / ``write_audit_event()`` deferred until the hash-chain
algorithm is specified (plan cites security doc; that section is empty).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE api_keys (
          id             text PRIMARY KEY,
          tenant_id      text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          name           text NOT NULL,
          hash           bytea NOT NULL,
          prefix         text NOT NULL,
          scopes         text[] NOT NULL,
          collection_ids text[],
          expires_at     timestamptz,
          last_used_at   timestamptz,
          created_by     text NOT NULL,
          created_at     timestamptz NOT NULL DEFAULT now(),
          revoked_at     timestamptz
        )
        """
    )
    op.execute("CREATE INDEX api_keys_tenant_idx ON api_keys(tenant_id)")
    op.execute("CREATE INDEX api_keys_prefix_idx ON api_keys(prefix)")

    op.execute(
        """
        CREATE TABLE collections (
          id                text PRIMARY KEY,
          tenant_id         text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          name              text NOT NULL,
          slug              citext NOT NULL,
          description       text,
          vector_backend    text NOT NULL DEFAULT 'pgvector'
                            CHECK (vector_backend IN ('pgvector','qdrant')),
          qdrant_collection text,
          index_status      text NOT NULL DEFAULT 'idle'
                            CHECK (index_status IN ('idle','building','ready','error')),
          index_version     int NOT NULL DEFAULT 0,
          policy            jsonb NOT NULL DEFAULT '{}',
          created_at        timestamptz NOT NULL DEFAULT now(),
          deleted_at        timestamptz,
          UNIQUE (tenant_id, slug)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE documents (
          id                 text PRIMARY KEY,
          tenant_id          text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          collection_id      text NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
          title              text NOT NULL,
          slug               citext NOT NULL,
          source_uri         text NOT NULL,
          source_mime        text NOT NULL,
          source_bytes       bigint NOT NULL,
          source_sha256      text NOT NULL,
          page_count         int,
          language           text,
          tags               text[] NOT NULL DEFAULT '{}',
          aliases            citext[] NOT NULL DEFAULT '{}',
          acl_principals     text[] NOT NULL DEFAULT '{}',
          sensitivity_label  text,
          status             text NOT NULL
                             CHECK (status IN (
                               'queued','parsing','ready_for_review','indexing',
                               'ready','failed','archived'
                             )),
          parse_backend      text,
          quality_score      float,
          needs_review_count int NOT NULL DEFAULT 0,
          version            int NOT NULL DEFAULT 1,
          metadata           jsonb NOT NULL DEFAULT '{}',
          frontmatter        jsonb NOT NULL DEFAULT '{}',
          created_at         timestamptz NOT NULL DEFAULT now(),
          created_by         text NOT NULL,
          finalized_at       timestamptz,
          deleted_at         timestamptz,
          UNIQUE (collection_id, slug),
          UNIQUE (collection_id, source_sha256)
        )
        """
    )
    op.execute("CREATE INDEX documents_tenant_idx ON documents(tenant_id)")
    op.execute("CREATE INDEX documents_collection_status_idx ON documents(collection_id, status)")
    op.execute("CREATE INDEX documents_tags_idx ON documents USING gin(tags)")
    op.execute("CREATE INDEX documents_frontmatter_idx ON documents USING gin(frontmatter)")

    op.execute(
        """
        CREATE TABLE jobs (
          id            text PRIMARY KEY,
          tenant_id     text NOT NULL,
          collection_id text,
          document_id   text,
          kind          text NOT NULL,
          status        text NOT NULL
                        CHECK (status IN (
                          'queued','running','waiting_review',
                          'succeeded','failed','cancelled'
                        )),
          progress      float NOT NULL DEFAULT 0,
          error         jsonb,
          taskiq_id     text,
          started_at    timestamptz,
          finished_at   timestamptz,
          created_at    timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX jobs_tenant_status_idx ON jobs(tenant_id, status)")

    for table in ("api_keys", "collections", "documents", "jobs"):
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
    for table in ("jobs", "documents", "collections", "api_keys"):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"DROP TABLE IF EXISTS {table}")
