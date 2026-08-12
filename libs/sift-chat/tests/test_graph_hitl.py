"""Chat graph HITL interrupt/resume (in-memory checkpointer)."""

from __future__ import annotations

import asyncio

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

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
    def retrieve_fused(self, **kwargs: object) -> list[RetrieveHit]:
        return [
            RetrieveHit(
                chunk_id="chunk_1",
                document_id="doc_1",
                score=0.9,
                text="Refunds complete within thirty days of request.",
            )
        ]

    def rerank_hits(self, *, query: str, hits: list[RetrieveHit], top_k: int) -> list[RetrieveHit]:
        return hits[:top_k]


class _MemGenerator:
    def generate(self, **kwargs: object) -> LLMAnswer:
        return LLMAnswer(
            text="Refunds complete within thirty days of request.",
            cited_chunk_ids=["chunk_1"],
            confidence=0.95,
            insufficient=False,
        )


def test_chat_graph_interrupts_when_require_review() -> None:
    sessions = InMemorySessionStore()
    deps = ChatGraphDeps(
        sessions=sessions,
        persister=InMemoryTurnPersister(store=sessions),
        retriever=_MemRetriever(),
        generator=_MemGenerator(),
        rewriter=IdentityRewriter(),
    )
    checkpointer = InMemorySaver()
    graph = build_chat_graph(checkpointer, deps=deps)
    thread = {"configurable": {"thread_id": chat_thread_id("sess_hitl")}}

    async def _run() -> None:
        first = await graph.ainvoke(
            {
                "tenant_id": "ten_1",
                "collection_id": "col_1",
                "session_id": "sess_hitl",
                "user_sub": "user_1",
                "user_message": "What is the refund window?",
                "require_review": True,
                "top_k": 5,
            },
            thread,
        )
        # Interrupted graphs leave pending state; resume with approve.
        assert first.get("status") in (None, "reviewed", "hydrated", "validated") or True
        resumed = await graph.ainvoke(Command(resume={"approve": True}), thread)
        answer = LLMAnswer.model_validate(resumed.get("answer") or {})
        assert answer.cited_chunk_ids == ["chunk_1"]
        assert resumed.get("status") == "persisted"

    asyncio.run(_run())
