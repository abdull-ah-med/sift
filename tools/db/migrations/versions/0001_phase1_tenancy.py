"""Phase 1 tenancy foundation: extensions, roles, orgs/tenants/users, RLS.

Revision ID: 0001
Revises:
Create Date: 2026-08-11

Bootstrap indexes are created in-transaction (tables are empty). Online
``CONCURRENTLY`` indexes apply to later migrations on populated tables.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS ltree")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # vector / pg_search ship with ParadeDB; tolerate plain Postgres images.
    op.execute(
        """
        DO $$
        BEGIN
          CREATE EXTENSION IF NOT EXISTS vector;
        EXCEPTION WHEN OTHERS THEN
          RAISE NOTICE 'vector extension skipped: %', SQLERRM;
        END
        $$
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          CREATE EXTENSION IF NOT EXISTS pg_search;
        EXCEPTION WHEN OTHERS THEN
          RAISE NOTICE 'pg_search extension skipped: %', SQLERRM;
        END
        $$
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
          CREATE ROLE sift_admin NOLOGIN;
        EXCEPTION WHEN duplicate_object THEN
          NULL;
        END
        $$
        """
    )
    op.execute("ALTER ROLE sift_admin BYPASSRLS")
    op.execute(
        """
        DO $$
        BEGIN
          CREATE ROLE sift_app NOLOGIN;
        EXCEPTION WHEN duplicate_object THEN
          NULL;
        END
        $$
        """
    )
    op.execute("ALTER ROLE sift_app NOBYPASSRLS")
    # Dev/superuser can SET ROLE sift_app for RLS-faithful sessions.
    op.execute(
        """
        DO $$
        BEGIN
          GRANT sift_app TO CURRENT_USER;
          GRANT sift_admin TO CURRENT_USER;
        EXCEPTION WHEN undefined_object OR invalid_grant_operation THEN
          NULL;
        END
        $$
        """
    )

    op.execute(
        """
        CREATE TABLE organizations (
          id            text PRIMARY KEY,
          name          text NOT NULL,
          slug          citext NOT NULL UNIQUE,
          sso_issuer    text,
          sso_audience  text,
          created_at    timestamptz NOT NULL DEFAULT now(),
          deleted_at    timestamptz
        )
        """
    )

    op.execute(
        """
        CREATE TABLE tenants (
          id              text PRIMARY KEY,
          organization_id text NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
          name            text NOT NULL,
          slug            citext NOT NULL,
          settings        jsonb NOT NULL DEFAULT '{}',
          quota           jsonb NOT NULL DEFAULT '{}',
          created_at      timestamptz NOT NULL DEFAULT now(),
          deleted_at      timestamptz,
          UNIQUE (organization_id, slug)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE users_in_tenant (
          tenant_id  text NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
          user_sub   text NOT NULL,
          email      citext NOT NULL,
          role       text NOT NULL CHECK (role IN ('owner','admin','reviewer','member','viewer')),
          created_at timestamptz NOT NULL DEFAULT now(),
          PRIMARY KEY (tenant_id, user_sub)
        )
        """
    )

    op.execute("CREATE INDEX tenants_organization_idx ON tenants(organization_id)")
    op.execute("CREATE INDEX users_in_tenant_email_idx ON users_in_tenant(email)")

    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON tenants
          USING (id = current_setting('sift.tenant_id', true))
        """
    )

    op.execute("ALTER TABLE users_in_tenant ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users_in_tenant FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY users_in_tenant_isolation ON users_in_tenant
          USING (tenant_id = current_setting('sift.tenant_id', true))
        """
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON organizations TO sift_app, sift_admin")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO sift_app, sift_admin")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON users_in_tenant TO sift_app, sift_admin")
    op.execute("GRANT USAGE ON SCHEMA public TO sift_app, sift_admin")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS users_in_tenant_isolation ON users_in_tenant")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON tenants")
    op.execute("DROP TABLE IF EXISTS users_in_tenant")
    op.execute("DROP TABLE IF EXISTS tenants")
    op.execute("DROP TABLE IF EXISTS organizations")
    # Roles and extensions are left in place: other DBs/sessions may share them.
