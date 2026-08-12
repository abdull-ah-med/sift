"""Unit tests for RRF fusion (p3-4)."""

from __future__ import annotations

from sift_retrieve.rrf import rrf_fuse


def test_rrf_fuse_merges_ranked_lists_with_k60() -> None:
    dense = ["a", "b", "c"]
    bm25 = ["b", "d", "a"]
    fused = rrf_fuse([dense, bm25], k=60)
    # b appears in both → highest; a in both → next; then singles
    assert fused[0] == "b"
    assert set(fused[:4]) == {"a", "b", "c", "d"}
    assert len(fused) == 4


def test_rrf_fuse_respects_limit() -> None:
    dense = [f"d{i}" for i in range(20)]
    bm25 = [f"b{i}" for i in range(20)]
    fused = rrf_fuse([dense, bm25], k=60, limit=5)
    assert len(fused) == 5


def test_rrf_fuse_empty_lists() -> None:
    assert rrf_fuse([[], []], k=60) == []
    assert rrf_fuse([], k=60) == []
