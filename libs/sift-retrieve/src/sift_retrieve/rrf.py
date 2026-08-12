"""Reciprocal Rank Fusion."""

from __future__ import annotations

from collections import defaultdict

RRF_K = 60


def rrf_fuse(
    ranked_lists: list[list[str]],
    *,
    k: int = RRF_K,
    limit: int | None = None,
) -> list[str]:
    """Fuse ranked id lists with Reciprocal Rank Fusion.

    Score for id at rank ``r`` (0-based) in a list is ``1 / (k + r + 1)``.
    """
    scores: dict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked):
            scores[item_id] += 1.0 / (k + rank + 1)
    ordered = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)
    if limit is not None:
        return ordered[:limit]
    return ordered
