"""Offline chat / RAGAS proxy gates (phase3-ragas-longprobe + Phase 4 floors)."""

from __future__ import annotations

from sift_eval.ragas_stub import (
    CONTEXT_RECALL_MIN,
    FAITHFULNESS_MIN,
    assert_chat_eval_thresholds,
    citation_faithfulness,
    context_recall,
    score_offline,
    score_with_ragas,
)


def test_citation_faithfulness_proxy() -> None:
    assert (
        citation_faithfulness(
            {
                "cited_chunk_ids": ["a", "b"],
                "context_chunk_ids": ["a", "b", "c"],
            }
        )
        == 1.0
    )
    assert (
        citation_faithfulness(
            {
                "cited_chunk_ids": ["a", "x"],
                "context_chunk_ids": ["a"],
            }
        )
        == 0.5
    )


def test_context_recall_proxy() -> None:
    assert (
        context_recall(
            {
                "expected_chunk_ids": ["a", "b"],
                "context_chunk_ids": ["a", "b", "c"],
            }
        )
        == 1.0
    )


def test_score_offline_meets_phase4_thresholds() -> None:
    rows = [
        {
            "cited_chunk_ids": ["c1"],
            "context_chunk_ids": ["c1", "c2"],
            "expected_chunk_ids": ["c1"],
            "insufficient": False,
        },
        {
            "cited_chunk_ids": ["c2"],
            "context_chunk_ids": ["c2"],
            "expected_chunk_ids": ["c2"],
            "insufficient": False,
        },
        {
            # insufficient refusal with no citations is faithful
            "cited_chunk_ids": [],
            "context_chunk_ids": [],
            "expected_chunk_ids": [],
            "insufficient": True,
        },
    ]
    report = score_offline(rows)
    assert report["faithfulness"] >= FAITHFULNESS_MIN
    assert report["context_recall"] >= CONTEXT_RECALL_MIN
    assert_chat_eval_thresholds(report)


def test_score_with_ragas_falls_back_offline() -> None:
    report = score_with_ragas(
        [
            {
                "cited_chunk_ids": ["c1"],
                "context_chunk_ids": ["c1"],
                "expected_chunk_ids": ["c1"],
            }
        ]
    )
    assert report["mode"] == 0.0
    assert_chat_eval_thresholds(report)
