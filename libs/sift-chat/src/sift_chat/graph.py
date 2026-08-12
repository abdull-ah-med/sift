"""LangGraph collection-scoped RAG chat (Phase 4 §2)."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from sift_chat.budget import ContextChunk, budget_trim_context
from sift_chat.citations import validate_citations
from sift_chat.deps import (
    ChatGraphDeps,
    ChatGraphState,
    dicts_to_hits,
    facts_from_state,
    hits_to_chunks,
    hits_to_dicts,
)
from sift_chat.memory import turns_for_verbatim_window
from sift_chat.prompts import SYSTEM_PROMPT, build_user_prompt
from sift_chat.schemas import LLMAnswer


def chat_thread_id(session_id: str) -> str:
    """Stable LangGraph thread id for a chat session."""
    return f"chat:{session_id}"


def _hydrate_session(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    loaded = deps.sessions.load_session(
        session_id=state["session_id"],
        tenant_id=state["tenant_id"],
        turn_limit=deps.turn_limit,
    )
    turns = turns_for_verbatim_window(
        list(loaded.get("turns") or []),
        limit=deps.turn_limit,
    )
    history = [
        (str(t.get("role", "user")), str(t.get("content", ""))) for t in turns if t.get("content")
    ]
    return {
        **state,
        "turns": turns,
        "rolling_summary": loaded.get("rolling_summary"),
        "long_term_facts": list(loaded.get("long_term_facts") or []),
        "history": history,
        "status": "hydrated",
        "cancelled": False,
        "needs_summarize": False,
        "persist_turn": None,
        "answer": None,
        "insufficient": False,
        "max_context_tokens": int(
            state.get("max_context_tokens") or deps.default_max_context_tokens
        ),
        "top_k": int(state.get("top_k") or deps.default_top_k),
    }


def _maybe_query_rewrite(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    history = list(state.get("history") or [])
    message = state["user_message"]
    if deps.rewriter is None:
        query = message
    else:
        query = deps.rewriter.rewrite(
            user_message=message,
            history=history,
            rolling_summary=state.get("rolling_summary"),
        )
    return {**state, "retrieval_query": query, "status": "query_ready"}


def _retrieve_hybrid(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    hits = deps.retriever.retrieve_fused(
        query=state.get("retrieval_query") or state["user_message"],
        tenant_id=state["tenant_id"],
        collection_id=state["collection_id"],
        top_k=int(state.get("top_k") or deps.default_top_k),
    )
    return {**state, "hits": hits_to_dicts(hits), "status": "retrieved"}


def _rerank(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    hits = dicts_to_hits(list(state.get("hits") or []))
    ranked = deps.retriever.rerank_hits(
        query=state.get("retrieval_query") or state["user_message"],
        hits=hits,
        top_k=int(state.get("top_k") or deps.default_top_k),
    )
    return {**state, "hits": hits_to_dicts(ranked), "status": "reranked"}


def _budget_trim_context(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    _ = deps
    hits = dicts_to_hits(list(state.get("hits") or []))
    chunks = hits_to_chunks(hits)
    history = list(state.get("history") or [])
    facts = facts_from_state(list(state.get("long_term_facts") or []))
    kept_chunks, kept_history, kept_summary, kept_facts = budget_trim_context(
        system=SYSTEM_PROMPT,
        question=state["user_message"],
        chunks=chunks,
        history=history,
        rolling_summary=state.get("rolling_summary"),
        facts=facts,
        max_tokens=int(state.get("max_context_tokens") or 8_000),
    )
    return {
        **state,
        "chunks": [
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "text": c.text,
                "score": c.score,
            }
            for c in kept_chunks
        ],
        "history": kept_history,
        "trimmed_summary": kept_summary,
        "trimmed_facts": kept_facts,
        "status": "budgeted",
    }


def _generate_structured(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    chunk_rows = list(state.get("chunks") or [])
    chunks = [
        ContextChunk(
            chunk_id=str(r["chunk_id"]),
            document_id=str(r["document_id"]),
            text=str(r.get("text") or ""),
            score=float(r.get("score") or 0.0),
        )
        for r in chunk_rows
    ]
    user_prompt = build_user_prompt(
        question=state["user_message"],
        chunks=chunks,
        history=list(state.get("history") or []),
        rolling_summary=state.get("trimmed_summary"),
        facts=list(state.get("trimmed_facts") or []),
    )
    if not chunks:
        answer = LLMAnswer(
            text="Insufficient information in the collection to answer that question.",
            cited_chunk_ids=[],
            confidence=0.0,
            insufficient=True,
        )
    else:
        answer = deps.generator.generate(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            allowed_chunk_ids=[c.chunk_id for c in chunks],
        )
    return {
        **state,
        "answer": answer.model_dump(),
        "insufficient": answer.insufficient,
        "status": "generated",
    }


def _validate_citations(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    _ = deps
    raw = state.get("answer") or {}
    answer = LLMAnswer.model_validate(raw)
    allowed = [str(c["chunk_id"]) for c in (state.get("chunks") or [])]
    validated = validate_citations(answer, retrieved_chunk_ids=allowed)
    return {
        **state,
        "answer": validated.model_dump(),
        "insufficient": validated.insufficient,
        "status": "validated",
    }


def _route_policy(state: ChatGraphState) -> Literal["interrupt_for_review", "persist_turn"]:
    if state.get("require_review"):
        return "interrupt_for_review"
    return "persist_turn"


def _interrupt_for_review(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    _ = deps
    decision = interrupt(
        {
            "type": "chat_answer_review",
            "session_id": state["session_id"],
            "answer": state.get("answer"),
            "insufficient": state.get("insufficient", False),
        }
    )
    answer_raw = dict(state.get("answer") or {})
    # Clear require_review so validate → policy routes to persist (07 §2: J→H→ok).
    base: ChatGraphState = {**state, "require_review": False}
    if isinstance(decision, dict):
        if decision.get("reject"):
            return {
                **base,
                "status": "rejected",
                "cancelled": True,
                "answer": {
                    **answer_raw,
                    "text": str(decision.get("reason") or "Answer rejected by reviewer."),
                    "insufficient": True,
                    "cited_chunk_ids": [],
                    "confidence": float(answer_raw.get("confidence") or 0.0),
                },
                "insufficient": True,
            }
        patch = {
            k: decision[k]
            for k in ("text", "cited_chunk_ids", "confidence", "insufficient")
            if k in decision
        }
        if patch:
            answer = LLMAnswer.model_validate({**answer_raw, **patch})
            return {
                **base,
                "answer": answer.model_dump(),
                "insufficient": answer.insufficient,
                "status": "reviewed",
            }
    return {**base, "status": "reviewed"}


def _persist_turn(state: ChatGraphState, *, deps: ChatGraphDeps) -> ChatGraphState:
    if state.get("cancelled"):
        return {**state, "status": "cancelled", "needs_summarize": False}
    answer = LLMAnswer.model_validate(state.get("answer") or {})
    turn_id = deps.persister.persist(
        session_id=state["session_id"],
        tenant_id=state["tenant_id"],
        user_message=state["user_message"],
        answer=answer,
    )
    turns = list(state.get("turns") or [])
    needs_summarize = (len(turns) + 2) > deps.turn_limit
    return {
        **state,
        "persist_turn": {"turn_id": turn_id, "insufficient": answer.insufficient},
        "needs_summarize": needs_summarize,
        "status": "persisted",
        "insufficient": answer.insufficient,
    }


def build_chat_graph(checkpointer: Any, *, deps: ChatGraphDeps) -> Any:
    """Compile the chat StateGraph with the given checkpointer and deps."""

    def hydrate(state: ChatGraphState) -> ChatGraphState:
        return _hydrate_session(state, deps=deps)

    def rewrite(state: ChatGraphState) -> ChatGraphState:
        return _maybe_query_rewrite(state, deps=deps)

    def retrieve(state: ChatGraphState) -> ChatGraphState:
        return _retrieve_hybrid(state, deps=deps)

    def rerank(state: ChatGraphState) -> ChatGraphState:
        return _rerank(state, deps=deps)

    def budget(state: ChatGraphState) -> ChatGraphState:
        return _budget_trim_context(state, deps=deps)

    def generate(state: ChatGraphState) -> ChatGraphState:
        return _generate_structured(state, deps=deps)

    def validate(state: ChatGraphState) -> ChatGraphState:
        return _validate_citations(state, deps=deps)

    def review(state: ChatGraphState) -> ChatGraphState:
        return _interrupt_for_review(state, deps=deps)

    def persist(state: ChatGraphState) -> ChatGraphState:
        return _persist_turn(state, deps=deps)

    graph: StateGraph[ChatGraphState, None, ChatGraphState, ChatGraphState] = StateGraph(
        ChatGraphState
    )
    graph.add_node("hydrate_session", hydrate)
    graph.add_node("maybe_query_rewrite", rewrite)
    graph.add_node("retrieve_hybrid", retrieve)
    graph.add_node("rerank", rerank)
    graph.add_node("budget_trim_context", budget)
    graph.add_node("generate_structured", generate)
    graph.add_node("validate_citations", validate)
    graph.add_node("interrupt_for_review", review)
    graph.add_node("persist_turn", persist)

    graph.add_edge(START, "hydrate_session")
    graph.add_edge("hydrate_session", "maybe_query_rewrite")
    graph.add_edge("maybe_query_rewrite", "retrieve_hybrid")
    graph.add_edge("retrieve_hybrid", "rerank")
    graph.add_edge("rerank", "budget_trim_context")
    graph.add_edge("budget_trim_context", "generate_structured")
    graph.add_edge("generate_structured", "validate_citations")
    graph.add_conditional_edges(
        "validate_citations",
        _route_policy,
        {
            "interrupt_for_review": "interrupt_for_review",
            "persist_turn": "persist_turn",
        },
    )
    graph.add_edge("interrupt_for_review", "validate_citations")
    graph.add_edge("persist_turn", END)
    return graph.compile(checkpointer=checkpointer)
