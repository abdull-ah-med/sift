"""LangGraph HITL document-review graph (Phase 2 §4.3).

Flow::

    start → auto_assess → route(need_review?)
      yes → interrupt(block_batch) → decision → assess_more (loop) → done
      no  → done

Checkpointer: ``langgraph-checkpoint-postgres`` (see ``sift_api.checkpointer``).
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from sift_core.models import ReviewState

_OPEN_REVIEW = frozenset(
    {
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
    """Return block ids still open for HITL review, ordered by ordinal if present."""
    open_blocks = [b for b in blocks if str(b.get("review_state", "")) in _OPEN_REVIEW]
    open_blocks.sort(key=lambda b: int(b.get("ordinal", 0)))
    return [str(b["id"]) for b in open_blocks]


def _auto_assess(state: ReviewGraphState) -> ReviewGraphState:
    if not state["pending_block_ids"]:
        return {**state, "status": "no_review_needed", "last_decisions": None}
    return {**state, "status": "pending_review"}


def _route_after_assess(state: ReviewGraphState) -> Literal["human_review", "done"]:
    if not state["pending_block_ids"]:
        return "done"
    return "human_review"


def _human_review(state: ReviewGraphState) -> ReviewGraphState:
    decision = interrupt(
        {
            "type": "block_review",
            "document_id": state["document_id"],
            "block_batch": list(state["pending_block_ids"]),
        }
    )
    if isinstance(decision, list):
        decisions = decision
    elif isinstance(decision, dict):
        raw = decision.get("decisions", decision)
        decisions = raw if isinstance(raw, list) else [decision]
    else:
        decisions = []
    return {**state, "last_decisions": decisions}


def _apply_decisions(state: ReviewGraphState) -> ReviewGraphState:
    decided = {
        str(item.get("block_id"))
        for item in (state.get("last_decisions") or [])
        if isinstance(item, dict) and item.get("block_id")
    }
    remaining = [bid for bid in state["pending_block_ids"] if bid not in decided]
    status = "complete" if not remaining else "pending_review"
    return {**state, "pending_block_ids": remaining, "status": status}


def _route_after_apply(state: ReviewGraphState) -> Literal["human_review", "done"]:
    if state["pending_block_ids"]:
        return "human_review"
    return "done"


def build_review_graph(checkpointer: Any) -> Any:
    """Compile the review StateGraph with the given checkpointer."""
    graph: StateGraph[ReviewGraphState, None, ReviewGraphState, ReviewGraphState] = StateGraph(
        ReviewGraphState
    )
    graph.add_node("auto_assess", _auto_assess)
    graph.add_node("human_review", _human_review)
    graph.add_node("apply_decisions", _apply_decisions)

    graph.add_edge(START, "auto_assess")
    graph.add_conditional_edges(
        "auto_assess",
        _route_after_assess,
        {"human_review": "human_review", "done": END},
    )
    graph.add_edge("human_review", "apply_decisions")
    graph.add_conditional_edges(
        "apply_decisions",
        _route_after_apply,
        {"human_review": "human_review", "done": END},
    )
    return graph.compile(checkpointer=checkpointer)


def _result_from_invoke(document_id: str, result: dict[str, Any]) -> dict[str, Any]:
    interrupts = result.get("__interrupt__") or []
    block_batch: list[str] | None = None
    if interrupts:
        payload = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
        if isinstance(payload, dict):
            raw_batch = payload.get("block_batch")
            if isinstance(raw_batch, list):
                block_batch = [str(x) for x in raw_batch]
        status = "pending_review"
        pending = block_batch or list(result.get("pending_block_ids") or [])
    else:
        status = str(result.get("status") or "complete")
        if status == "no_review_needed":
            status = "no_review_needed"
        elif status != "pending_review":
            status = "complete"
        pending = list(result.get("pending_block_ids") or [])

    out: dict[str, Any] = {
        "thread_id": review_thread_id(document_id),
        "document_id": document_id,
        "status": status,
        "pending_block_ids": pending,
    }
    if block_batch is not None:
        out["block_batch"] = block_batch
    elif status == "pending_review":
        out["block_batch"] = pending
    return out


async def start_document_review(
    *,
    checkpointer: Any,
    tenant_id: str,
    document_id: str,
    block_ids: list[str],
) -> dict[str, Any]:
    """Start (or re-enter) review; returns interrupt payload or completion."""
    graph = build_review_graph(checkpointer)
    config = {"configurable": {"thread_id": review_thread_id(document_id)}}
    initial: ReviewGraphState = {
        "tenant_id": tenant_id,
        "document_id": document_id,
        "pending_block_ids": list(block_ids),
        "status": "pending_review" if block_ids else "no_review_needed",
        "last_decisions": None,
    }
    result = await graph.ainvoke(initial, config=config)
    return _result_from_invoke(document_id, result)


async def resume_document_review(
    *,
    checkpointer: Any,
    document_id: str,
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resume an interrupted review with a decision batch."""
    graph = build_review_graph(checkpointer)
    config = {"configurable": {"thread_id": review_thread_id(document_id)}}
    result = await graph.ainvoke(Command(resume=decisions), config=config)
    return _result_from_invoke(document_id, result)
