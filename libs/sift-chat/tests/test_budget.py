"""Unit tests for token budget trimming."""

from __future__ import annotations

from sift_chat.budget import ContextChunk, budget_trim_context, estimate_tokens


def test_estimate_tokens_empty() -> None:
    assert estimate_tokens("") == 0


def test_budget_keeps_chunks_before_history() -> None:
    chunks = [
        ContextChunk(chunk_id="c1", document_id="d1", text="alpha " * 20),
        ContextChunk(chunk_id="c2", document_id="d1", text="beta " * 20),
    ]
    history = [("user", "old question " * 30), ("assistant", "old answer " * 30)]
    kept_chunks, kept_history, summary, facts = budget_trim_context(
        system="sys",
        question="q",
        chunks=chunks,
        history=history,
        rolling_summary="summary text",
        facts=["fact one"],
        max_tokens=80,
    )
    assert kept_chunks
    assert kept_chunks[0].chunk_id == "c1"
    # With a tight budget, older history may be dropped after chunks.
    assert isinstance(kept_history, list)
    assert summary is None or isinstance(summary, str)
    assert isinstance(facts, list)


def test_budget_zero_remaining_returns_empty() -> None:
    kept_chunks, kept_history, summary, facts = budget_trim_context(
        system="x" * 200,
        question="y" * 200,
        chunks=[ContextChunk(chunk_id="c1", document_id="d1", text="body")],
        history=[("user", "hi")],
        rolling_summary="sum",
        facts=["f"],
        max_tokens=10,
    )
    assert kept_chunks == []
    assert kept_history == []
    assert summary is None
    assert facts == []
