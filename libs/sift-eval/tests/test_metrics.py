"""Unit tests for retrieve eval metrics (p3-7)."""

from __future__ import annotations

from sift_eval.metrics import mrr_at_k, recall_at_k, score_run


def test_recall_at_10_full_hit() -> None:
    ranked = ["c1", "c2", "c3"]
    assert recall_at_k(ranked, expected=["c2"], k=10) == 1.0


def test_recall_at_k_miss() -> None:
    assert recall_at_k(["a", "b"], expected=["z"], k=10) == 0.0


def test_mrr_at_k_first_rank() -> None:
    assert mrr_at_k(["hit", "other"], expected=["hit"], k=10) == 1.0


def test_mrr_at_k_second_rank() -> None:
    assert mrr_at_k(["x", "hit"], expected=["hit"], k=10) == 0.5


def test_score_run_aggregates_queries() -> None:
    report = score_run(
        [
            {"query": "q1", "ranked_ids": ["a", "b"], "expected_ids": ["b"]},
            {"query": "q2", "ranked_ids": ["c"], "expected_ids": ["z"]},
        ],
        k=10,
    )
    assert report["recall_at_k"] == 0.5
    assert report["mrr_at_k"] == 0.25
    assert report["n_queries"] == 2
