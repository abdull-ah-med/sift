"""LangGraph HITL document-review graph (Phase 2 §4.3).

Flow::

    start → auto_assess → route(need_review?)
      yes → interrupt(block_batch) → decision → assess_more (loop) → done
      no  → done

Checkpointer: ``langgraph-checkpoint-postgres`` (see ``sift_api.checkpointer``).
"""

from __future__ import annotations

from typing import Any, TypedDict

from sift_core.models import ReviewState

_OPEN_REVIEW = frozenset(
    {
        ReviewState.PENDING.value,
        ReviewState.NEEDS_REVIEW.value,
        ReviewState.IN_REVIEW.value,
        ReviewState.CONFLICT.value,
    }
)


class ReviewGraphState(TypedDict):
    """State flowing through the document-review graph."""

    tenant_id: str
    document_id: str
    pending_block_ids: list[str]
    status: str  # pending_review | complete | no_review_needed
    last_decisions: list[dict[str, Any]] | None


def review_thread_id(document_id: str) -> str:
    """Stable LangGraph thread id for a document review session."""
    return f"doc-review:{document_id}"


def pending_block_ids(blocks: list[dict[str, Any]]) -> list[str]:
    """Return block ids still open for HITL review, ordered by ordinal if present.

    TDD stub — returns empty until the impl commit.
    """
    del blocks
    return []


def build_review_graph(checkpointer: Any) -> Any:
    """Compile the review StateGraph with the given checkpointer.

    TDD stub — real graph lands in the impl commit.
    """
    del checkpointer
    raise NotImplementedError("TDD stub — review graph not compiled yet")


async def start_document_review(
    *,
    checkpointer: Any,
    tenant_id: str,
    document_id: str,
    block_ids: list[str],
) -> dict[str, Any]:
    """Start (or re-enter) review; returns interrupt payload or completion.

    TDD stub — always reports complete until the impl commit.
    """
    del checkpointer, tenant_id, block_ids
    return {
        "thread_id": review_thread_id(document_id),
        "document_id": document_id,
        "status": "complete",
        "pending_block_ids": [],
    }


async def resume_document_review(
    *,
    checkpointer: Any,
    document_id: str,
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resume an interrupted review with a decision batch.

    TDD stub — always reports complete until the impl commit.
    """
    del checkpointer, decisions
    return {
        "thread_id": review_thread_id(document_id),
        "document_id": document_id,
        "status": "complete",
        "pending_block_ids": [],
    }
