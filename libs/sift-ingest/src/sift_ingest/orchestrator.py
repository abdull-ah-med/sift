"""Taskiq-native ingest orchestration surface (absorbs vendor orchestrator).

The API registers documents and enqueues ``ingest_document``; the worker is
the sole parse path. This module names the ordered stages for callers and
tests without reintroducing sync ingest on the request path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IngestStage(StrEnum):
    FETCH = "fetch"
    PARSE = "parse"
    PII = "pii"
    EQUATION_FLAGS = "equation_flags"
    PERSIST_BLOCKS = "persist_blocks"
    CHUNK = "chunk"
    QUALITY_SCORE = "quality_score"
    CROSS_REFERENCE = "cross_reference"
    SUMMARY_ENRICH = "summary_enrich"
    FINALIZE = "finalize"


@dataclass(frozen=True, slots=True)
class IngestPlan:
    """Ordered stages executed by the worker for one document."""

    document_id: str
    job_id: str
    tenant_id: str
    stages: tuple[IngestStage, ...] = (
        IngestStage.FETCH,
        IngestStage.PARSE,
        IngestStage.PII,
        IngestStage.EQUATION_FLAGS,
        IngestStage.PERSIST_BLOCKS,
        IngestStage.CHUNK,
        IngestStage.QUALITY_SCORE,
        IngestStage.CROSS_REFERENCE,
        IngestStage.SUMMARY_ENRICH,
        IngestStage.FINALIZE,
    )


def plan_ingest(*, document_id: str, job_id: str, tenant_id: str) -> IngestPlan:
    """Return the canonical worker stage plan for a queued ingest job."""
    return IngestPlan(document_id=document_id, job_id=job_id, tenant_id=tenant_id)


def taskiq_task_name() -> str:
    """Taskiq task name registered on ``sift_api.tasks.ingest_document``."""
    return "ingest_document"
