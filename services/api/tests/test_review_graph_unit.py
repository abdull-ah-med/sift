"""TDD: LangGraph document-review graph contracts (Phase 2 §4.3)."""

from __future__ import annotations

import pytest

from sift_api.review_graph import (
    pending_block_ids,
    resume_document_review,
    review_thread_id,
    start_document_review,
)


def test_review_thread_id_is_namespaced() -> None:
    assert review_thread_id("doc_01ABC") == "doc-review:doc_01ABC"


def test_pending_block_ids_keeps_open_review_states_only() -> None:
    blocks = [
        {"id": "b1", "ordinal": 2, "review_state": "approved"},
        {"id": "b2", "ordinal": 0, "review_state": "needs_review"},
        {"id": "b3", "ordinal": 1, "review_state": "in_review"},
        {"id": "b4", "ordinal": 3, "review_state": "rejected"},
        {"id": "b5", "ordinal": 4, "review_state": "pending"},
        {"id": "b6", "ordinal": 5, "review_state": "conflict"},
        {"id": "b7", "ordinal": 6, "review_state": "edited"},
    ]
    assert pending_block_ids(blocks) == ["b2", "b3", "b5", "b6"]


@pytest.mark.asyncio
async def test_start_interrupts_when_blocks_need_review() -> None:
    from langgraph.checkpoint.memory import InMemorySaver

    checkpointer = InMemorySaver()
    result = await start_document_review(
        checkpointer=checkpointer,
        tenant_id="ten_1",
        document_id="doc_1",
        block_ids=["b_needs"],
    )
    assert result["status"] == "pending_review"
    assert result["thread_id"] == "doc-review:doc_1"
    assert result["pending_block_ids"] == ["b_needs"]
    assert "block_batch" in result


@pytest.mark.asyncio
async def test_start_completes_when_no_blocks_need_review() -> None:
    from langgraph.checkpoint.memory import InMemorySaver

    checkpointer = InMemorySaver()
    result = await start_document_review(
        checkpointer=checkpointer,
        tenant_id="ten_1",
        document_id="doc_2",
        block_ids=[],
    )
    assert result["status"] in {"complete", "no_review_needed"}
    assert result["pending_block_ids"] == []


@pytest.mark.asyncio
async def test_resume_applies_decisions_and_completes() -> None:
    from langgraph.checkpoint.memory import InMemorySaver

    checkpointer = InMemorySaver()
    started = await start_document_review(
        checkpointer=checkpointer,
        tenant_id="ten_1",
        document_id="doc_3",
        block_ids=["b1", "b2"],
    )
    assert started["status"] == "pending_review"

    resumed = await resume_document_review(
        checkpointer=checkpointer,
        document_id="doc_3",
        decisions=[
            {"block_id": "b1", "action": "approve"},
            {"block_id": "b2", "action": "reject"},
        ],
    )
    assert resumed["status"] == "complete"
    assert resumed["pending_block_ids"] == []
