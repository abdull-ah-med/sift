"""Retrieval eval metrics (Phase 3 §6) — no LLM required."""

from __future__ import annotations

from typing import Any


def recall_at_k(ranked_ids: list[str], *, expected: list[str], k: int) -> float:
    """Fraction of expected ids appearing in the top-``k`` ranked list."""
    if not expected:
        return 1.0
    top = set(ranked_ids[:k])
    hits = sum(1 for e in expected if e in top)
    return hits / len(expected)


def mrr_at_k(ranked_ids: list[str], *, expected: list[str], k: int) -> float:
    """Mean reciprocal rank of the first expected id within top-``k``."""
    if not expected:
        return 1.0
    expected_set = set(expected)
    for i, item in enumerate(ranked_ids[:k]):
        if item in expected_set:
            return 1.0 / (i + 1)
    return 0.0


def score_run(rows: list[dict[str, Any]], *, k: int = 10) -> dict[str, float | int]:
    """Aggregate recall@k and MRR@k over query rows."""
    if not rows:
        return {"recall_at_k": 1.0, "mrr_at_k": 1.0, "n_queries": 0, "k": k}
    recalls: list[float] = []
    mrrs: list[float] = []
    for row in rows:
        ranked = list(row.get("ranked_ids") or [])
        expected = list(row.get("expected_ids") or row.get("expected_chunk_ids") or [])
        recalls.append(recall_at_k(ranked, expected=expected, k=k))
        mrrs.append(mrr_at_k(ranked, expected=expected, k=k))
    n = len(rows)
    return {
        "recall_at_k": sum(recalls) / n,
        "mrr_at_k": sum(mrrs) / n,
        "n_queries": n,
        "k": k,
    }
