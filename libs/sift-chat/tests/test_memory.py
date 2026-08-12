"""Unit tests for three-layer session memory helpers."""

from __future__ import annotations

from sift_chat.memory import (
    condense_turns_extractive,
    dedupe_facts,
    extract_facts_from_answer,
    merge_rolling_summary,
    should_summarize,
    turns_for_verbatim_window,
    turns_needing_summary,
)
from sift_core.models import LongTermFact


def test_verbatim_window_keeps_tail() -> None:
    turns = [{"role": "user", "content": str(i)} for i in range(15)]
    kept = turns_for_verbatim_window(turns, limit=12)
    assert len(kept) == 12
    assert kept[0]["content"] == "3"


def test_turns_needing_summary() -> None:
    turns = [{"role": "user", "content": str(i)} for i in range(14)]
    older = turns_needing_summary(turns, limit=12)
    assert len(older) == 2
    assert older[0]["content"] == "0"


def test_should_summarize() -> None:
    assert should_summarize(12) is False
    assert should_summarize(13) is True


def test_condense_and_merge() -> None:
    block = condense_turns_extractive([{"role": "user", "content": "Hello world from user"}])
    assert "user:" in block
    merged = merge_rolling_summary("prior", block)
    assert "prior" in merged and "---" in merged


def test_dedupe_facts() -> None:
    facts = dedupe_facts(
        [
            LongTermFact(text="Same", source_chunk_id="c1", confidence=0.9),
            LongTermFact(text="same", source_chunk_id="c1", confidence=0.5),
            LongTermFact(text="Other", source_chunk_id="c2", confidence=0.8),
        ]
    )
    assert len(facts) == 2


def test_extract_facts_requires_citations() -> None:
    assert extract_facts_from_answer(answer_text="A long enough sentence here.", cited_chunk_ids=[], confidence=0.9) == []
    facts = extract_facts_from_answer(
        answer_text="Retention is thirty days. Deletion follows notice.",
        cited_chunk_ids=["chunk_1"],
        confidence=0.9,
    )
    assert len(facts) >= 1
    assert facts[0].source_chunk_id == "chunk_1"
