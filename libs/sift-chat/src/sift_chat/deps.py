"""Injectable ports and LangGraph state for collection-scoped RAG chat."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TypedDict

from sift_chat.budget import ContextChunk
from sift_chat.schemas import LLMAnswer
from sift_core.models import LongTermFact
from sift_retrieve.hybrid import RetrieveHit


class ChatGraphState(TypedDict, total=False):
    """State flowing through the chat graph."""

    tenant_id: str
    collection_id: str
    session_id: str
    user_sub: str
    user_message: str
    retrieval_query: str
    require_review: bool
    max_context_tokens: int
    top_k: int
    turns: list[dict[str, Any]]
    rolling_summary: str | None
    long_term_facts: list[dict[str, Any]]
    hits: list[dict[str, Any]]
    chunks: list[dict[str, Any]]
    history: list[tuple[str, str]]
    trimmed_summary: str | None
    trimmed_facts: list[str]
    answer: dict[str, Any] | None
    insufficient: bool
    status: str
    needs_summarize: bool
    persist_turn: dict[str, Any] | None
    cancelled: bool


class SessionStore(Protocol):
    """Load session memory layers for ``hydrate_session``."""

    def load_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        turn_limit: int = 12,
    ) -> dict[str, Any]:
        """Return session fields + recent turns (role/content dicts)."""


class TurnPersister(Protocol):
    """Persist the assistant/user turn after validation."""

    def persist(  # noqa: PLR0913 — matches TurnPersister
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_message: str,
        answer: LLMAnswer,
        latency_ms: int | None = None,
        langfuse_trace_id: str | None = None,
    ) -> str:
        """Insert turns; return assistant turn id."""


class QueryRewriter(Protocol):
    """Optional LLM rewrite of the retrieval query."""

    def rewrite(
        self,
        *,
        user_message: str,
        history: list[tuple[str, str]],
        rolling_summary: str | None,
    ) -> str: ...


class HybridRetrievePort(Protocol):
    """Thin port over ``HybridRetriever`` (split retrieve vs rerank)."""

    def retrieve_fused(
        self,
        *,
        query: str,
        tenant_id: str,
        collection_id: str,
        top_k: int,
    ) -> list[RetrieveHit]: ...

    def rerank_hits(
        self,
        *,
        query: str,
        hits: list[RetrieveHit],
        top_k: int,
    ) -> list[RetrieveHit]: ...


class AnswerGenerator(Protocol):
    """Produce a structured ``LLMAnswer`` from prompts + chunks."""

    def generate(
        self,
        *,
        system: str,
        user: str,
        allowed_chunk_ids: list[str],
    ) -> LLMAnswer: ...


@dataclass
class ChatGraphDeps:
    """Runtime dependencies injected when compiling the chat graph."""

    sessions: SessionStore
    persister: TurnPersister
    retriever: HybridRetrievePort
    generator: AnswerGenerator
    rewriter: QueryRewriter | None = None
    turn_limit: int = 12
    default_max_context_tokens: int = 8_000
    default_top_k: int = 10


def hits_to_dicts(hits: list[RetrieveHit]) -> list[dict[str, Any]]:
    """Serialize retrieve hits into graph-safe dicts."""
    return [
        {
            "chunk_id": h.chunk_id,
            "document_id": h.document_id,
            "score": h.score,
            "rerank_score": h.rerank_score,
            "text": h.text or "",
        }
        for h in hits
    ]


def dicts_to_hits(rows: list[dict[str, Any]]) -> list[RetrieveHit]:
    """Deserialize graph hit dicts back to ``RetrieveHit``."""
    return [
        RetrieveHit(
            chunk_id=str(r["chunk_id"]),
            document_id=str(r["document_id"]),
            score=float(r.get("score") or 0.0),
            rerank_score=(float(r["rerank_score"]) if r.get("rerank_score") is not None else None),
            text=str(r.get("text") or "") or None,
        )
        for r in rows
    ]


def hits_to_chunks(hits: list[RetrieveHit]) -> list[ContextChunk]:
    """Map retrieve hits to budget/prompt chunks."""
    return [
        ContextChunk(
            chunk_id=h.chunk_id,
            document_id=h.document_id,
            text=h.text or "",
            score=float(h.rerank_score if h.rerank_score is not None else h.score),
        )
        for h in hits
    ]


@dataclass
class HybridRetrieverAdapter:
    """Adapt ``HybridRetriever`` to the chat retrieve/rerank port."""

    retriever: Any
    candidate_limit: int = 50

    def retrieve_fused(
        self,
        *,
        query: str,
        tenant_id: str,
        collection_id: str,
        top_k: int,
    ) -> list[RetrieveHit]:
        return self.retriever.retrieve(
            query=query,
            tenant_id=tenant_id,
            collection_id=collection_id,
            top_k=max(top_k, self.candidate_limit),
            rerank=False,
        )

    def rerank_hits(
        self,
        *,
        query: str,
        hits: list[RetrieveHit],
        top_k: int,
    ) -> list[RetrieveHit]:
        if not hits:
            return []
        # Re-run retrieve with rerank enabled using the same query; prefer
        # in-memory rerank when the underlying retriever exposes a reranker.
        reranker = getattr(self.retriever, "_reranker", None)
        load_texts = getattr(self.retriever, "_load_texts", None)
        if reranker is None:
            return hits[:top_k]
        texts = load_texts([h.chunk_id for h in hits]) if callable(load_texts) else {}
        docs = [(h.chunk_id, texts.get(h.chunk_id, h.text or "")) for h in hits]
        if not any(text for _cid, text in docs):
            return hits[:top_k]
        ranked = reranker.rerank(query=query, documents=docs)
        by_id = {h.chunk_id: h for h in hits}
        out: list[RetrieveHit] = []
        for cid, rscore in ranked[:top_k]:
            base = by_id.get(cid)
            if base is None:
                continue
            out.append(
                RetrieveHit(
                    chunk_id=base.chunk_id,
                    document_id=base.document_id,
                    score=base.score,
                    rerank_score=rscore,
                    text=texts.get(cid, base.text),
                )
            )
        return out or hits[:top_k]


@dataclass
class InstructorAnswerGenerator:
    """``AnswerGenerator`` backed by the Instructor client patch."""

    client: Any
    model: str
    max_tokens: int = 1024

    def generate(
        self,
        *,
        system: str,
        user: str,
        allowed_chunk_ids: list[str],
    ) -> LLMAnswer:
        # Import locally so importing sift_chat does not require a live provider.
        # allowed_chunk_ids reserved for prompt hardening / future constrained decoding.
        _ = allowed_chunk_ids
        return self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_model=LLMAnswer,
        )


@dataclass
class IdentityRewriter:
    """No-op rewriter — retrieval query equals the user message."""

    def rewrite(
        self,
        *,
        user_message: str,
        history: list[tuple[str, str]],
        rolling_summary: str | None,
    ) -> str:
        _ = history, rolling_summary
        return user_message


@dataclass
class InMemorySessionStore:
    """Test/smoke session store (not for production API wiring)."""

    sessions: dict[str, dict[str, Any]] = field(default_factory=dict)

    def load_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        turn_limit: int = 12,
    ) -> dict[str, Any]:
        row = self.sessions.get(session_id) or {
            "tenant_id": tenant_id,
            "rolling_summary": None,
            "long_term_facts": [],
            "turns": [],
        }
        turns = list(row.get("turns") or [])[-turn_limit:]
        return {
            "rolling_summary": row.get("rolling_summary"),
            "long_term_facts": list(row.get("long_term_facts") or []),
            "turns": turns,
        }


@dataclass
class InMemoryTurnPersister:
    """Test/smoke persister that records turns in memory."""

    store: InMemorySessionStore
    _n: int = 0

    def persist(  # noqa: PLR0913 — matches TurnPersister
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_message: str,
        answer: LLMAnswer,
        latency_ms: int | None = None,
        langfuse_trace_id: str | None = None,
    ) -> str:
        _ = tenant_id, latency_ms, langfuse_trace_id
        self._n += 1
        turn_id = f"turn_mem_{self._n}"
        row = self.store.sessions.setdefault(
            session_id,
            {"rolling_summary": None, "long_term_facts": [], "turns": []},
        )
        turns = list(row.get("turns") or [])
        turns.append({"role": "user", "content": user_message})
        turns.append(
            {
                "role": "assistant",
                "content": answer.text,
                "cited_chunk_ids": list(answer.cited_chunk_ids),
                "turn_id": turn_id,
            }
        )
        row["turns"] = turns
        return turn_id


def facts_from_state(raw: list[dict[str, Any]] | list[LongTermFact]) -> list[str]:
    """Extract fact text lines from state or domain models."""
    out: list[str] = []
    for item in raw:
        if isinstance(item, LongTermFact):
            out.append(item.text)
        elif isinstance(item, dict) and item.get("text"):
            out.append(str(item["text"]))
    return out
