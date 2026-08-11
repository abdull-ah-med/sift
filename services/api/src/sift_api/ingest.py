"""Ingest entrypoint: fetch object → parse → persist blocks."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from sift.parse import DigitalPdfParser, ParseConfig, Parser
from sift_api.db import sync_dsn
from sift_api.ingest_parse import run_ingest_parse
from sift_api.settings import Settings, get_settings
from sift_api.storage import download_object
from sift_core.audit import write_audit_event


def _mark_ingest_failed(
    eng: Engine,
    *,
    document_id: str,
    job_id: str,
    tenant_id: str,
    error: Exception,
) -> None:
    now = datetime.now(UTC)
    with eng.begin() as conn:
        conn.execute(text("SET LOCAL ROLE sift_admin"))
        conn.execute(
            text(
                """
                UPDATE documents
                SET status = 'failed'
                WHERE id = :document_id AND tenant_id = :tenant_id
                """
            ),
            {"document_id": document_id, "tenant_id": tenant_id},
        )
        conn.execute(
            text(
                """
                UPDATE jobs
                SET status = 'failed',
                    progress = 1.0,
                    finished_at = :now,
                    error = CAST(:error AS jsonb)
                WHERE id = :job_id AND tenant_id = :tenant_id
                  AND status NOT IN ('succeeded', 'cancelled')
                """
            ),
            {
                "now": now,
                "job_id": job_id,
                "tenant_id": tenant_id,
                "error": json.dumps({"message": str(error), "type": type(error).__name__}),
            },
        )
        write_audit_event(
            conn,
            tenant_id=tenant_id,
            actor="system",
            action="document.ingest_parse_failed",
            target_kind="document",
            target_id=document_id,
            payload={"job_id": job_id, "error_type": type(error).__name__},
        )


def run_ingest_document(
    *,
    document_id: str,
    job_id: str,
    tenant_id: str,
    parser: Parser | None = None,
    source_path: Path | None = None,
    parse_config: ParseConfig | None = None,
    require_review: bool | None = None,
    settings: Settings | None = None,
) -> str:
    """Run Phase 2 ingest for one document.

    If ``source_path`` is provided (tests), skip object-store download.
    Otherwise load ``documents.source_uri`` and fetch from SeaweedFS.
    """
    cfg = settings or get_settings()
    eng = create_engine(sync_dsn(cfg))
    try:
        local_path = source_path
        policy_require_review = bool(require_review) if require_review is not None else False
        if local_path is None:
            with eng.begin() as conn:
                conn.execute(text("SET LOCAL ROLE sift_admin"))
                row = (
                    conn.execute(
                        text(
                            """
                            SELECT d.source_uri, c.policy
                            FROM documents d
                            JOIN collections c ON c.id = d.collection_id
                            WHERE d.id = :document_id AND d.tenant_id = :tenant_id
                            """
                        ),
                        {"document_id": document_id, "tenant_id": tenant_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    return "missing"
                source_uri = row["source_uri"]
                policy = row["policy"] or {}
                if require_review is None and isinstance(policy, dict):
                    policy_require_review = bool(policy.get("require_review", False))
                    threshold = policy.get("confidence_threshold")
                    if threshold is not None and parse_config is None:
                        parse_config = ParseConfig(confidence_threshold=float(threshold))

            suffix = Path(str(source_uri)).suffix or ".bin"
            try:
                with tempfile.TemporaryDirectory(prefix="sift-ingest-") as tmp:
                    dest = Path(tmp) / f"original{suffix}"
                    download_object(source_uri=source_uri, dest=dest, settings=cfg)
                    return run_ingest_parse(
                        document_id=document_id,
                        job_id=job_id,
                        tenant_id=tenant_id,
                        engine=eng,
                        source_path=dest,
                        parser=parser or DigitalPdfParser(),
                        parse_config=parse_config,
                        require_review=policy_require_review,
                    )
            except Exception as exc:
                _mark_ingest_failed(
                    eng,
                    document_id=document_id,
                    job_id=job_id,
                    tenant_id=tenant_id,
                    error=exc,
                )
                raise

        return run_ingest_parse(
            document_id=document_id,
            job_id=job_id,
            tenant_id=tenant_id,
            engine=eng,
            source_path=local_path,
            parser=parser or DigitalPdfParser(),
            parse_config=parse_config,
            require_review=policy_require_review,
        )
    finally:
        eng.dispose()
