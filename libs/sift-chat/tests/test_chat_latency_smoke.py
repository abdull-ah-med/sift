"""Lightweight chat turn latency smoke (no network LLM)."""

from __future__ import annotations

import asyncio
import time

from langgraph.checkpoint.memory import InMemorySaver

from sift_chat import (
    ChatGraphDeps,
    IdentityRewriter,
    InMemorySessionStore,
    InMemoryTurnPersister,
    LLMAnswer,
    build_chat_graph,
    chat_thread_id,
)
from sift_retrieve.hybrid import RetrieveHit

# Sanity ceiling for in-process mocked graph (laptop gate; not a prod SLO).
P95_MS_CEILING = 2_000.0


class _MemRetriever:
    def retrieve_fused(self, **kwargs: object) -> list[RetrieveHit]:
        return [
            RetrieveHit(chunk_id="c1", document_id="d1", score=1.0, text="alpha beta gamma")
        ]

    def rerank_hits(self, *, query: str, hits: list[RetrieveHit], top_k: int) -> list[RetrieveHit]:
        return hits[:top_k]


class _MemGenerator:
    def generate(self, **kwargs: object) -> LLMAnswer:
        return LLMAnswer(text="alpha beta gamma", cited_chunk_ids=["c1"], confidence=1.0)


def test_chat_turn_latency_smoke_under_ceiling() -> None:
    sessions = InMemorySessionStore()
    deps = ChatGraphDeps(
        sessions=sessions,
        persister=InMemoryTurnPersister(store=sessions),
        retriever=_MemRetriever(),
        generator=_MemGenerator(),
        rewriter=IdentityRewriter(),
    )
    graph = build_chat_graph(InMemorySaver(), deps=deps)
    samples: list[float] = []

    async def once(i: int) -> None:
        t0 = time.perf_counter()
        await graph.ainvoke(
            {
                "tenant_id": "ten_1",
                "collection_id": "col_1",
                "session_id": f"sess_{i}",
                "user_sub": "u",
                "user_message": "q",
                "require_review": False,
                "top_k": 3,
            },
            {"configurable": {"thread_id": chat_thread_id(f"sess_{i}")}},
        )
        samples.append((time.perf_counter() - t0) * 1000.0)

    async def run() -> None:
        for i in range(8):
            await once(i)

    asyncio.run(run())
    samples.sort()
    p95 = samples[int(0.95 * (len(samples) - 1))]
    assert p95 < P95_MS_CEILING, f"chat turn p95 {p95:.1f}ms >= {P95_MS_CEILING}ms"
