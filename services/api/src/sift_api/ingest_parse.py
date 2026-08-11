"""Persist ParseResult blocks and drive document status transitions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from sqlalchemy import Connection, text
from sqlalchemy.engine import Engine

from sift.parse import DigitalPdfParser, ParseConfig, Parser, ParseResult
from sift_core.audit import write_audit_event
from sift_core.models import ReviewState


class ObjectFetcher(Protocol):
    """Fetch a stored object to a local path for parsing."""

    def fetch_to_path(self, *, source_uri: str, dest: Path) -> Path: ...


def document_status_after_parse(
    result: ParseResult,
    *,
    require_review: bool = False,
) -> str:
    """Choose documents.status after blocks are written."""
    needs = sum(1 for b in result.blocks if b.review_state is ReviewState.NEEDS_REVIEW)
    if require_review or needs > 0:
        return "ready_for_review"
    return "indexing"


def insert_blocks(
    conn: Connection,
    *,
    tenant_id: str,
    document_id: str,
    result: ParseResult,
) -> int:
    """Insert parse blocks; returns count of needs_review rows."""
    needs_review = 0
    for block in result.blocks:
        if block.review_state is ReviewState.NEEDS_REVIEW:
            needs_review += 1
        hierarchy = (
            json.dumps({"section_path": block.hierarchy}) if block.hierarchy is not None else None
        )
        conn.execute(
            text(
                """
                INSERT INTO blocks (
                  id, tenant_id, document_id, ordinal, block_type, text, html,
                  provenance, confidence, hierarchy, cross_refs,
                  table_data, figure_data, formula_data, pii_map,
                  review_state, version
                ) VALUES (
                  :id, :tenant_id, :document_id, :ordinal, :block_type, :text, :html,
                  CAST(:provenance AS jsonb), :confidence, CAST(:hierarchy AS jsonb),
                  :cross_refs,
                  CAST(:table_data AS jsonb), CAST(:figure_data AS jsonb),
                  CAST(:formula_data AS jsonb), CAST(:pii_map AS jsonb),
                  :review_state, :version
                )
                """
            ),
            {
                "id": block.id,
                "tenant_id": tenant_id,
                "document_id": document_id,
                "ordinal": block.ordinal,
                "block_type": block.block_type.value,
                "text": block.text,
                "html": block.html,
                "provenance": block.provenance.model_dump_json(),
                "confidence": block.confidence,
                "hierarchy": hierarchy,
                "cross_refs": block.cross_refs,
                "table_data": json.dumps(block.table_data) if block.table_data else None,
                "figure_data": json.dumps(block.figure_data) if block.figure_data else None,
                "formula_data": (json.dumps(block.formula_data) if block.formula_data else None),
                "pii_map": json.dumps(block.pii_map) if block.pii_map else None,
                "review_state": block.review_state.value,
                "version": block.version,
            },
        )
    return needs_review


def run_ingest_parse(
    *,
    document_id: str,
    job_id: str,
    tenant_id: str,
    engine: Engine,
    source_path: Path,
    parser: Parser | None = None,
    parse_config: ParseConfig | None = None,
    require_review: bool = False,
) -> str:
    """Parse ``source_path``, persist blocks, update job/document status.

    Returns the resulting document status.
    """
    active_parser: Parser = parser or DigitalPdfParser()
    config = parse_config or ParseConfig()

    with engine.begin() as conn:
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
            return "skipped"

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
                SET status = 'parsing', parse_backend = :backend
                WHERE id = :document_id AND tenant_id = :tenant_id
                """
            ),
            {
                "document_id": document_id,
                "tenant_id": tenant_id,
                "backend": type(active_parser).__name__,
            },
        )

        try:
            result = active_parser.parse(source_path, config)
            needs_review = insert_blocks(
                conn,
                tenant_id=tenant_id,
                document_id=document_id,
                result=result,
            )
            status = document_status_after_parse(result, require_review=require_review)
            finished = datetime.now(UTC)
            conn.execute(
                text(
                    """
                    UPDATE documents
                    SET status = :status,
                        page_count = :page_count,
                        needs_review_count = :needs_review
                    WHERE id = :document_id AND tenant_id = :tenant_id
                    """
                ),
                {
                    "status": status,
                    "page_count": result.metadata.page_count,
                    "needs_review": needs_review,
                    "document_id": document_id,
                    "tenant_id": tenant_id,
                },
            )
            job_status = "waiting_review" if status == "ready_for_review" else "succeeded"
            conn.execute(
                text(
                    """
                    UPDATE jobs
                    SET status = :job_status, progress = 1.0, finished_at = :now
                    WHERE id = :job_id
                    """
                ),
                {"job_status": job_status, "now": finished, "job_id": job_id},
            )
            write_audit_event(
                conn,
                tenant_id=tenant_id,
                actor="system",
                action="document.ingest_parse",
                target_kind="document",
                target_id=document_id,
                payload={
                    "job_id": job_id,
                    "status": status,
                    "block_count": len(result.blocks),
                    "needs_review_count": needs_review,
                },
            )
            return status
        except Exception as exc:
            failed = datetime.now(UTC)
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
                    WHERE id = :job_id
                    """
                ),
                {
                    "now": failed,
                    "job_id": job_id,
                    "error": json.dumps({"message": str(exc), "type": type(exc).__name__}),
                },
            )
            write_audit_event(
                conn,
                tenant_id=tenant_id,
                actor="system",
                action="document.ingest_parse_failed",
                target_kind="document",
                target_id=document_id,
                payload={"job_id": job_id, "error_type": type(exc).__name__},
            )
            raise
