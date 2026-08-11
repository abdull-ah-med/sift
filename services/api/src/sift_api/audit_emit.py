"""Sync audit emit helper for API mutations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine, text

from sift_api.db import sync_dsn
from sift_core.audit import write_audit_event


def emit_audit(
    *,
    tenant_id: str,
    actor: str,
    action: str,
    target_kind: str,
    target_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    eng = create_engine(sync_dsn())
    try:
        with eng.begin() as conn:
            conn.execute(text("SET LOCAL ROLE sift_admin"))
            write_audit_event(
                conn,
                tenant_id=tenant_id,
                actor=actor,
                action=action,
                target_kind=target_kind,
                target_id=target_id,
                payload=payload or {},
            )
    finally:
        eng.dispose()
