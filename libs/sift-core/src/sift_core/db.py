"""Database session helpers (tenant GUC for RLS)."""

from __future__ import annotations

from collections.abc import Iterable


def tenant_guc_statements(
    tenant_id: str,
    *,
    principals: Iterable[str] | None = None,
) -> list[str]:
    """Return SQL to set per-transaction tenant context for RLS.

    Application code must run these inside a transaction (``set_config(..., true)``
    is ``SET LOCAL``) so the GUC never leaks across pooled connections.
    """
    statements = [
        f"SELECT set_config('sift.tenant_id', {_sql_str(tenant_id)}, true)",
    ]
    if principals is not None:
        array_literal = _text_array_literal(principals)
        statements.append(f"SELECT set_config('sift.principals', {_sql_str(array_literal)}, true)")
    return statements


def _sql_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _text_array_literal(values: Iterable[str]) -> str:
    escaped = [v.replace("\\", "\\\\").replace('"', '\\"') for v in values]
    inner = ",".join(f'"{v}"' for v in escaped)
    return "{" + inner + "}"
