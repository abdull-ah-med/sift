#!/usr/bin/env python3
"""Dev bootstrap: org + tenant + admin API key (prints raw key once).

Usage (from repo root, Postgres up, migrations applied)::

    export SIFT_API_KEY_PEPPER='dev-pepper-change-me'
    uv run python tools/db/seed/dev_bootstrap.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime

from sqlalchemy import create_engine, text

from sift_core.audit import write_audit_event
from sift_core.auth.api_keys import mint_api_key
from sift_core.ids import IdKind, new_id


def _dsn() -> str:
    raw = os.environ.get("SIFT_PG_DSN", "postgresql+psycopg://sift:sift@127.0.0.1:5432/sift")
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql+asyncpg://")
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql://")
    return raw


def main() -> int:
    pepper = os.environ.get("SIFT_API_KEY_PEPPER", "").encode("utf-8")
    if not pepper:
        print("Set SIFT_API_KEY_PEPPER", file=sys.stderr)
        return 1
    eng = create_engine(_dsn())
    org_id = new_id(IdKind.ORGANIZATION)
    tenant_id = new_id(IdKind.TENANT)
    key_id = new_id(IdKind.API_KEY)
    minted = mint_api_key(pepper)
    now = datetime.now(UTC)
    scopes = [
        "documents:read",
        "documents:write",
        "search",
        "vault:read",
        "export",
        "chat",
    ]
    with eng.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text(
                """
                INSERT INTO organizations (id, name, slug, created_at)
                VALUES (:id, 'Dev Org', 'dev', :now)
                """
            ),
            {"id": org_id, "now": now},
        )
        conn.execute(
            text(
                """
                INSERT INTO tenants (id, organization_id, name, slug, created_at)
                VALUES (:id, :org, 'Dev Tenant', 'dev', :now)
                """
            ),
            {"id": tenant_id, "org": org_id, "now": now},
        )
        conn.execute(
            text(
                """
                INSERT INTO api_keys (
                  id, tenant_id, name, hash, hash_version, prefix, scopes,
                  created_by, created_at
                ) VALUES (
                  :id, :tenant_id, 'bootstrap', :hash, :hash_version, :prefix, :scopes,
                  'seed', :now
                )
                """
            ),
            {
                "id": key_id,
                "tenant_id": tenant_id,
                "hash": minted.hash,
                "hash_version": minted.hash_version,
                "prefix": minted.prefix,
                "scopes": scopes,
                "now": now,
            },
        )
        write_audit_event(
            conn,
            tenant_id=tenant_id,
            actor="seed",
            action="tenant.create",
            target_kind="tenant",
            target_id=tenant_id,
            payload={"tenant_name": "Dev Tenant", "created_by": "seed"},
        )
    eng.dispose()
    print(f"organization_id={org_id}")
    print(f"tenant_id={tenant_id}")
    print(f"api_key_id={key_id}")
    print(f"raw_key={minted.raw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
