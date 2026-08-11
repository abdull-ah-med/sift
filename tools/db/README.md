# db

Alembic migrations for the sift Postgres schema.

## Commands

From the repo root:

```bash
# Apply all migrations
uv run alembic -c tools/db/alembic.ini upgrade head

# Roll back one revision
uv run alembic -c tools/db/alembic.ini downgrade -1

# Show current revision
uv run alembic -c tools/db/alembic.ini current
```

DSN resolution (first match wins):

1. `SIFT_PG_DSN` (async `postgresql+asyncpg://...` is rewritten to psycopg)
2. `DATABASE_URL`
3. Default: `postgresql+psycopg://sift:sift@127.0.0.1:5432/sift`

## Roles

Migration `0001` creates:

- `sift_admin` — `BYPASSRLS` (migrations / break-glass)
- `sift_app` — no bypass; subject to tenant RLS

Application sessions must `SET ROLE sift_app` (or connect as a login role that inherits it) and `SET LOCAL sift.tenant_id` every transaction.

## Seed

```bash
export SIFT_API_KEY_PEPPER=dev-pepper-change-me
uv run alembic -c tools/db/alembic.ini upgrade head
uv run python tools/db/seed/dev_bootstrap.py
```

Prints a one-time `raw_key` for local CLI/UI login.

## Revisions

| Rev | Contents |
|-----|----------|
| `0001` | extensions, `sift_app`/`sift_admin`, organizations, tenants, users_in_tenant + RLS |
| `0002` | api_keys, collections, documents, jobs + RLS |
| `0003` | audit_events + RLS (hashing in `sift_core.audit`, ADR-0014) |
| `0004` | `api_keys.hash_version` (ADR-0013 pepper rotation) |
