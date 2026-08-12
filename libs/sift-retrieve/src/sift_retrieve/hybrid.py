"""Hybrid dense + BM25 → RRF → optional rerank."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class RetrieveHit:
    chunk_id: str
    document_id: str
    score: float
    rerank_score: float | None = None
    text: str | None = None


class _Searcher(Protocol):
    def search(self, **kwargs: Any) -> list[RetrieveHit]: ...


class HybridRetriever:
    def __init__(self, **_kwargs: Any) -> None:
        raise NotImplementedError

    def retrieve(self, **_kwargs: Any) -> list[RetrieveHit]:
        raise NotImplementedError
