"""Ingest stub shared by API (inline) and Taskiq worker."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine, text

from sift_api.settings import get_settings
from sift_core.audit import write_audit_event


def _sync_dsn() -> str:
    raw = get_settings().sift_pg_dsn
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql+asyncpg://")
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql://")
    return raw


def run_ingest_stub(*, document_id: str, job_id: str, tenant_id: str) -> None:
    """Mark document ready and job succeeded; emit audit event (Phase 1 stub)."""
    eng = create_engine(_sync_dsn())
    try:
        with eng.begin() as conn:
            conn.execute(text("SET LOCAL ROLE sift_admin"))
            row = (
                conn.execute(
                    text(
                        """
                    SELECT status FROM jobs
                    WHERE id = :job_id AND tenant_id = :tenant_id
                    """
                    ),
                    {"job_id": job_id, "tenant_id": tenant_id},
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["status"] in {"succeeded", "cancelled"}:
                return
            now = datetime.now(UTC)
            conn.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = 'running', started_at = :now, progress = 0.1
                    WHERE id = :job_id
                    """
                ),
                {"job_id": job_id, "now": now},
            )
            conn.execute(
                text(
                    """
                    UPDATE documents
                    SET status = 'ready', finalized_at = :now
                    WHERE id = :document_id AND tenant_id = :tenant_id
                    """
                ),
                {"document_id": document_id, "tenant_id": tenant_id, "now": now},
            )
            conn.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = 'succeeded', progress = 1.0, finished_at = :now
                    WHERE id = :job_id
                    """
                ),
                {"job_id": job_id, "now": now},
            )
            write_audit_event(
                conn,
                tenant_id=tenant_id,
                actor="system",
                action="document.ingest_stub",
                target_kind="document",
                target_id=document_id,
                payload={"job_id": job_id, "status": "ready"},
            )
    finally:
        eng.dispose()
