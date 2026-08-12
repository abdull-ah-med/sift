"""Graph compile smoke — no live LLM required."""

from __future__ import annotations

import asyncio

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


class _MemRetriever:
    def retrieve_fused(
        self,
        *,
        query: str,
        tenant_id: str,
        collection_id: str,
        top_k: int,
    ) -> list[RetrieveHit]:
        return [
            RetrieveHit(
                chunk_id="chunk_1",
                document_id="doc_1",
                score=0.9,
                text="Refunds complete within thirty days of request.",
            )
        ]

    def rerank_hits(
        self,
        *,
        query: str,
        hits: list[RetrieveHit],
        top_k: int,
    ) -> list[RetrieveHit]:
        return hits[:top_k]


class _MemGenerator:
    def generate(
        self,
        *,
        system: str,
        user: str,
        allowed_chunk_ids: list[str],
    ) -> LLMAnswer:
        return LLMAnswer(
            text="Refunds complete within thirty days of request.",
            cited_chunk_ids=["chunk_1"],
            confidence=0.95,
            insufficient=False,
        )


def test_chat_thread_id() -> None:
    assert chat_thread_id("sess_1") == "chat:sess_1"


def test_build_chat_graph_compiles() -> None:
    sessions = InMemorySessionStore()
    deps = ChatGraphDeps(
        sessions=sessions,
        persister=InMemoryTurnPersister(store=sessions),
        retriever=_MemRetriever(),
        generator=_MemGenerator(),
        rewriter=IdentityRewriter(),
    )
    graph = build_chat_graph(InMemorySaver(), deps=deps)
    assert graph is not None


def test_graph_ainvoke_grounded_path() -> None:
    sessions = InMemorySessionStore()
    deps = ChatGraphDeps(
        sessions=sessions,
        persister=InMemoryTurnPersister(store=sessions),
        retriever=_MemRetriever(),
        generator=_MemGenerator(),
        rewriter=IdentityRewriter(),
    )
    graph = build_chat_graph(InMemorySaver(), deps=deps)

    async def _run() -> dict:
        return await graph.ainvoke(
            {
                "tenant_id": "ten_1",
                "collection_id": "col_1",
                "session_id": "sess_1",
                "user_sub": "user_1",
                "user_message": "What is the refund window?",
                "require_review": False,
                "top_k": 5,
            },
            {"configurable": {"thread_id": chat_thread_id("sess_1")}},
        )

    result = asyncio.run(_run())
    answer = LLMAnswer.model_validate(result.get("answer") or {})
    assert answer.cited_chunk_ids == ["chunk_1"]
    assert answer.insufficient is False
    assert "thirty days" in answer.text.lower()
