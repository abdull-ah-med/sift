"""Reciprocal Rank Fusion."""

from __future__ import annotations

RRF_K = 60


def rrf_fuse(
    ranked_lists: list[list[str]],
    *,
    k: int = RRF_K,
    limit: int | None = None,
) -> list[str]:
    raise NotImplementedError
