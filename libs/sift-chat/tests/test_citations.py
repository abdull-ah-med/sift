"""Unit tests for citation validation."""

from __future__ import annotations

from sift_chat.citations import validate_citations
from sift_chat.schemas import LLMAnswer


def test_drops_hallucinated_chunk_ids() -> None:
    answer = LLMAnswer(
        text="Refunds take 30 days.",
        cited_chunk_ids=["chunk_a", "chunk_fake"],
        confidence=0.9,
        insufficient=False,
    )
    out = validate_citations(answer, retrieved_chunk_ids=["chunk_a", "chunk_b"])
    assert out.cited_chunk_ids == ["chunk_a"]
    assert out.insufficient is False


def test_all_citations_dropped_marks_insufficient() -> None:
    answer = LLMAnswer(
        text="Invented answer.",
        cited_chunk_ids=["chunk_x"],
        confidence=0.5,
        insufficient=False,
    )
    out = validate_citations(answer, retrieved_chunk_ids=["chunk_a"])
    assert out.cited_chunk_ids == []
    assert out.insufficient is True
    assert out.text == ""


def test_grounded_claim_without_citations_insufficient() -> None:
    answer = LLMAnswer(
        text="The policy requires notice.",
        cited_chunk_ids=[],
        confidence=0.8,
        insufficient=False,
    )
    out = validate_citations(answer, retrieved_chunk_ids=["chunk_a"])
    assert out.insufficient is True
    assert out.text == ""


def test_empty_retrieval_preserves_explicit_insufficient() -> None:
    answer = LLMAnswer(text="", cited_chunk_ids=[], confidence=0.0, insufficient=True)
    out = validate_citations(answer, retrieved_chunk_ids=[])
    assert out.insufficient is True
