"""Collection-scoped chat REST + SSE (Phase 4 §6)."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated, Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from langgraph.types import Command
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.ext.asyncio import AsyncSession
from ulid import ULID

from sift_api.audit_emit import emit_audit
from sift_api.auth import AuthContext, require_scopes, tenant_db
from sift_api.db import sync_dsn
from sift_api.schemas import (
    ChatAskRequest,
    ChatCitationOut,
    ChatResumeRequest,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionOut,
    ChatTurnOut,
)
from sift_api.search import _hybrid_retrieve, query_hash
from sift_api.settings import Settings, get_settings
from sift_api.tasks import extract_facts, summarize_session
from sift_chat import (
    ChatGraphDeps,
    IdentityRewriter,
    InstructorAnswerGenerator,
    LLMAnswer,
    build_chat_graph,
    chat_thread_id,
)
from sift_chat.schemas import LLMAnswer as AnswerModel
from sift_core.ids import IdKind, new_id
from sift_retrieve.hybrid import RetrieveHit

router = APIRouter(prefix="/v1", tags=["chat"])

_log = logging.getLogger(__name__)
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_CHAT_LLM_TIMEOUT_S = 60.0
_NO_LLM_TEXT = (
    "No chat LLM is configured because neither OPENAI_API_KEY, ANTHROPIC_API_KEY, "
    "nor a loopback SIFT_CHAT_BASE_URL is set. Run ollama serve, then ollama pull "
    "llama3.1, and set SIFT_CHAT_BASE_URL=http://127.0.0.1:11434/v1. (err_chat_no_llm)"
)
_BAD_URL_TEXT = (
    "Chat LLM base URL was rejected because it is not an http loopback address "
    "(127.0.0.1, localhost, or ::1). Set SIFT_CHAT_BASE_URL=http://127.0.0.1:11434/v1. "
    "(err_chat_llm_url)"
)


def _new_turn_id() -> str:
    return f"turn_{ULID()}"


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n"


def _sync_engine(settings: Settings) -> Engine:
    return create_engine(sync_dsn(settings), pool_pre_ping=True)


def _with_tenant(conn: Connection, tenant_id: str) -> None:
    conn.execute(text("SET LOCAL ROLE sift_app"))
    conn.execute(
        text("SELECT set_config('sift.tenant_id', :tid, true)"),
        {"tid": tenant_id},
    )


class _SearchRetriever:
    """HybridRetrievePort backed by Phase 3 search orchestration."""

    def __init__(self, *, settings: Settings, engine: Engine) -> None:
        self._settings = settings
        self._engine = engine

    def retrieve_fused(
        self,
        *,
        query: str,
        tenant_id: str,
        collection_id: str,
        top_k: int,
    ) -> list[RetrieveHit]:
        hits, meta = _hybrid_retrieve(
            query=query,
            tenant_id=tenant_id,
            collection_id=collection_id,
            top_k=max(top_k, 50),
            document_ids=None,
            rerank=False,
            settings=self._settings,
            engine=self._engine,
        )
        out: list[RetrieveHit] = []
        for hit in hits:
            text_body = str(meta.get(hit.chunk_id, {}).get("text") or "")
            out.append(
                RetrieveHit(
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    score=hit.score,
                    text=text_body or None,
                )
            )
        return out

    def rerank_hits(
        self,
        *,
        query: str,
        hits: list[RetrieveHit],
        top_k: int,
    ) -> list[RetrieveHit]:
        if not hits:
            return []
        from sift_retrieve.rerank import TeiReranker

        docs = [(h.chunk_id, h.text or "") for h in hits]
        if not any(t for _c, t in docs):
            return hits[:top_k]
        reranker = TeiReranker(base_url=self._settings.sift_tei_rerank_url)
        ordered = reranker.rerank(query=query, documents=docs)
        by_id = {h.chunk_id: h for h in hits}
        out: list[RetrieveHit] = []
        for cid, score in ordered[:top_k]:
            base = by_id.get(cid)
            if base is None:
                continue
            out.append(
                RetrieveHit(
                    chunk_id=base.chunk_id,
                    document_id=base.document_id,
                    score=base.score,
                    rerank_score=score,
                    text=base.text,
                )
            )
        return out or hits[:top_k]


class _PgSessionStore:
    def __init__(self, *, engine: Engine, turn_limit: int) -> None:
        self._engine = engine
        self._turn_limit = turn_limit

    def load_session(
        self,
        *,
        session_id: str,
        tenant_id: str,
        turn_limit: int = 12,
    ) -> dict[str, Any]:
        limit = turn_limit or self._turn_limit
        with self._engine.begin() as conn:
            _with_tenant(conn, tenant_id)
            row = (
                conn.execute(
                    text(
                        """
                        SELECT rolling_summary, long_term_facts
                        FROM chat_sessions
                        WHERE id = :id AND deleted_at IS NULL
                        """
                    ),
                    {"id": session_id},
                )
                .mappings()
                .first()
            )
            if row is None:
                return {"rolling_summary": None, "long_term_facts": [], "turns": []}
            turns = [
                dict(t)
                for t in conn.execute(
                    text(
                        """
                        SELECT role, content, cited_chunk_ids
                        FROM chat_turns
                        WHERE session_id = :sid
                        ORDER BY created_at DESC
                        LIMIT :lim
                        """
                    ),
                    {"sid": session_id, "lim": limit},
                ).mappings()
            ]
            turns.reverse()
            return {
                "rolling_summary": row["rolling_summary"],
                "long_term_facts": list(row["long_term_facts"] or []),
                "turns": turns,
            }


class _PgTurnPersister:
    def __init__(self, *, engine: Engine) -> None:
        self._engine = engine
        self.last_turn_id: str | None = None

    def persist(  # noqa: PLR0913
        self,
        *,
        session_id: str,
        tenant_id: str,
        user_message: str,
        answer: AnswerModel,
        latency_ms: int | None = None,
        langfuse_trace_id: str | None = None,
    ) -> str:
        user_turn_id = _new_turn_id()
        assistant_turn_id = _new_turn_id()
        self.last_turn_id = assistant_turn_id
        now = datetime.now(UTC)
        docs: list[str] = []
        with self._engine.begin() as conn:
            _with_tenant(conn, tenant_id)
            conn.execute(
                text(
                    """
                    INSERT INTO chat_turns (
                      id, session_id, role, content, cited_chunk_ids, cited_documents,
                      usage, latency_ms, langfuse_trace_id, created_at
                    ) VALUES (
                      :id, :sid, 'user', :content, '{}', '{}', NULL, NULL, NULL, :ts
                    )
                    """
                ),
                {
                    "id": user_turn_id,
                    "sid": session_id,
                    "content": user_message,
                    "ts": now,
                },
            )
            conn.execute(
                text(
                    """
                    INSERT INTO chat_turns (
                      id, session_id, role, content, cited_chunk_ids, cited_documents,
                      usage, latency_ms, langfuse_trace_id, created_at
                    ) VALUES (
                      :id, :sid, 'assistant', :content, :cites, :docs,
                      NULL, :latency, :trace, :ts
                    )
                    """
                ),
                {
                    "id": assistant_turn_id,
                    "sid": session_id,
                    "content": answer.text,
                    "cites": list(answer.cited_chunk_ids),
                    "docs": docs,
                    "latency": latency_ms,
                    "trace": langfuse_trace_id,
                    "ts": now,
                },
            )
            conn.execute(
                text(
                    """
                    UPDATE chat_sessions
                    SET last_message_at = :ts
                    WHERE id = :sid
                    """
                ),
                {"ts": now, "sid": session_id},
            )
        return assistant_turn_id


def _loopback_openai_url(url: str) -> str:
    """Normalize an OpenAI-compatible base URL; reject anything that is not loopback http.

    Hostname must be an exact match for ``127.0.0.1``, ``localhost``, or ``::1``.
    Path gets ``/v1`` appended when missing. Query, fragment, and userinfo are dropped.
    """
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").rstrip(".").lower()
    if parts.scheme != "http" or host not in _LOOPBACK_HOSTS:
        msg = "chat LLM base URL must be http loopback"
        raise ValueError(msg)
    path = (parts.path or "").rstrip("/")
    if not path.endswith("/v1"):
        path = f"{path}/v1" if path else "/v1"
    netloc = f"[{host}]" if ":" in host else host
    if parts.port is not None:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit(("http", netloc, path, "", ""))


def _resolved_loopback_url(settings: Settings) -> str | None:
    """Return a validated loopback base URL, or None when local compat is not requested."""
    configured = settings.sift_chat_base_url.strip()
    if configured:
        return _loopback_openai_url(configured)
    if settings.sift_llm_provider.strip().lower() == "ollama":
        return _loopback_openai_url("http://127.0.0.1:11434/v1")
    return None


class _EnvAnswerGenerator:
    """Instructor generator: OpenAI, then Anthropic, then loopback OpenAI-compat."""

    def generate(
        self,
        *,
        system: str,
        user: str,
        allowed_chunk_ids: list[str],
    ) -> LLMAnswer:
        settings = get_settings()
        openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not openai_key and settings.sift_llm_provider.strip().lower() == "openai":
            openai_key = os.environ.get("SIFT_LLM_API_KEY", "").strip()
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if openai_key:
            import instructor
            from openai import OpenAI

            cloud_model = os.environ.get("SIFT_CHAT_MODEL", "").strip() or "gpt-4o-mini"
            client = instructor.from_openai(OpenAI(api_key=openai_key))
            return client.chat.completions.create(
                model=cloud_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_model=LLMAnswer,
            )
        if anthropic_key:
            import instructor
            from anthropic import Anthropic

            client = instructor.from_anthropic(Anthropic(api_key=anthropic_key))
            return client.messages.create(
                model=os.environ.get("SIFT_CHAT_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
                response_model=LLMAnswer,
            )
        try:
            base_url = _resolved_loopback_url(settings)
        except ValueError:
            _log.warning("chat_llm_url_rejected")
            return LLMAnswer(
                text=_BAD_URL_TEXT,
                cited_chunk_ids=[],
                confidence=0.0,
                insufficient=True,
            )
        if base_url:
            import instructor
            from openai import OpenAI

            api_key = settings.sift_chat_api_key.strip() or "ollama"
            client = instructor.from_openai(
                OpenAI(base_url=base_url, api_key=api_key, timeout=_CHAT_LLM_TIMEOUT_S),
                mode=instructor.Mode.JSON,
                max_retries=2,
            )
            return InstructorAnswerGenerator(
                client=client,
                model=settings.sift_chat_model,
            ).generate(
                system=system,
                user=user,
                allowed_chunk_ids=allowed_chunk_ids,
            )
        _ = allowed_chunk_ids
        return LLMAnswer(
            text=_NO_LLM_TEXT,
            cited_chunk_ids=[],
            confidence=0.0,
            insufficient=True,
        )


def _require_review_for_collection(conn: Connection, collection_id: str) -> bool:
    row = (
        conn.execute(
            text("SELECT policy FROM collections WHERE id = :id AND deleted_at IS NULL"),
            {"id": collection_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        return False
    policy = row.get("policy") or {}
    if isinstance(policy, str):
        policy = json.loads(policy)
    return bool(policy.get("require_review") or policy.get("chat_require_review"))


def _actor_sub(ctx: AuthContext) -> str:
    """Stable per-user key for session ownership (OIDC sub or API-key actor)."""
    return ctx.user_sub or ctx.actor


async def _ensure_collection(
    session: AsyncSession,
    collection_id: str,
) -> None:
    exists = (
        await session.execute(
            text("SELECT 1 FROM collections WHERE id = :id AND deleted_at IS NULL"),
            {"id": collection_id},
        )
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="collection not found")


@router.post(
    "/collections/{collection_id}/chat/sessions",
    response_model=ChatSessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_session(
    collection_id: str,
    body: ChatSessionCreate,
    ctx: Annotated[AuthContext, Depends(require_scopes("chat"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> ChatSessionOut:
    await _ensure_collection(session, collection_id)
    session_id = new_id(IdKind.SESSION)
    now = datetime.now(UTC)
    user_sub = _actor_sub(ctx)
    await session.execute(
        text(
            """
            INSERT INTO chat_sessions (
              id, tenant_id, collection_id, user_sub, title, long_term_facts, created_at
            ) VALUES (
              :id, :tenant_id, :collection_id, :user_sub, :title, '[]'::jsonb, :ts
            )
            """
        ),
        {
            "id": session_id,
            "tenant_id": ctx.tenant_id,
            "collection_id": collection_id,
            "user_sub": user_sub,
            "title": body.title,
            "ts": now,
        },
    )
    await session.commit()
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action="chat.session.create",
        target_kind="session",
        target_id=session_id,
        payload={"collection_id": collection_id},
    )
    return ChatSessionOut(
        id=session_id,
        collection_id=collection_id,
        title=body.title,
        created_at=now,
        last_message_at=None,
    )


@router.get(
    "/collections/{collection_id}/chat/sessions",
    response_model=list[ChatSessionOut],
)
async def list_chat_sessions(
    collection_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("chat"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> list[ChatSessionOut]:
    await _ensure_collection(session, collection_id)
    user_sub = _actor_sub(ctx)
    rows = (
        (
            await session.execute(
                text(
                    """
                    SELECT id, collection_id, title, created_at, last_message_at
                    FROM chat_sessions
                    WHERE collection_id = :cid
                      AND user_sub = :user_sub
                      AND deleted_at IS NULL
                    ORDER BY coalesce(last_message_at, created_at) DESC
                    """
                ),
                {"cid": collection_id, "user_sub": user_sub},
            )
        )
        .mappings()
        .all()
    )
    return [
        ChatSessionOut(
            id=str(r["id"]),
            collection_id=str(r["collection_id"]),
            title=r["title"],
            created_at=r["created_at"],
            last_message_at=r["last_message_at"],
        )
        for r in rows
    ]


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_chat_session(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("chat"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> ChatSessionDetail:
    user_sub = _actor_sub(ctx)
    row = (
        (
            await session.execute(
                text(
                    """
                    SELECT id, collection_id, title, rolling_summary, created_at, last_message_at
                    FROM chat_sessions
                    WHERE id = :id AND user_sub = :user_sub AND deleted_at IS NULL
                    """
                ),
                {"id": session_id, "user_sub": user_sub},
            )
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    turns = (
        (
            await session.execute(
                text(
                    """
                    SELECT id, role, content, cited_chunk_ids, cited_documents, created_at
                    FROM chat_turns
                    WHERE session_id = :sid
                    ORDER BY created_at ASC
                    """
                ),
                {"sid": session_id},
            )
        )
        .mappings()
        .all()
    )
    return ChatSessionDetail(
        id=str(row["id"]),
        collection_id=str(row["collection_id"]),
        title=row["title"],
        created_at=row["created_at"],
        last_message_at=row["last_message_at"],
        rolling_summary=row["rolling_summary"],
        turns=[
            ChatTurnOut(
                id=str(t["id"]),
                role=str(t["role"]),
                content=str(t["content"]),
                cited_chunk_ids=list(t["cited_chunk_ids"] or []),
                cited_documents=list(t["cited_documents"] or []),
                created_at=t["created_at"],
            )
            for t in turns
        ],
    )


@router.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("chat"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> None:
    user_sub = _actor_sub(ctx)
    result = await session.execute(
        text(
            """
            UPDATE chat_sessions
            SET deleted_at = :ts
            WHERE id = :id AND user_sub = :user_sub AND deleted_at IS NULL
            """
        ),
        {"id": session_id, "user_sub": user_sub, "ts": datetime.now(UTC)},
    )
    if int(getattr(result, "rowcount", 0) or 0) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    await session.commit()
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action="chat.session.delete",
        target_kind="session",
        target_id=session_id,
        payload={},
    )


@router.post("/collections/{collection_id}/chat")
async def chat_ask(  # noqa: PLR0915 — SSE orchestration
    collection_id: str,
    body: ChatAskRequest,
    request: Request,
    ctx: Annotated[AuthContext, Depends(require_scopes("chat"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> StreamingResponse:
    """Ask a collection-scoped question; streams SSE token/citation/usage/done events."""
    from sift_api.checkpointer import open_postgres_checkpointer

    await _ensure_collection(session, collection_id)
    settings = get_settings()
    session_id = body.session_id
    if session_id is None:
        created = await create_chat_session(
            collection_id,
            ChatSessionCreate(title=None),
            ctx,
            session,
        )
        session_id = created.id

    eng = _sync_engine(settings)
    with eng.begin() as conn:
        _with_tenant(conn, ctx.tenant_id)
        require_review = _require_review_for_collection(conn, collection_id)
        owned = conn.execute(
            text(
                """
                SELECT 1 FROM chat_sessions
                WHERE id = :id
                  AND collection_id = :cid
                  AND user_sub = :user_sub
                  AND deleted_at IS NULL
                """
            ),
            {"id": session_id, "cid": collection_id, "user_sub": _actor_sub(ctx)},
        ).first()
        if owned is None:
            eng.dispose()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")

    persister = _PgTurnPersister(engine=eng)
    deps = ChatGraphDeps(
        sessions=_PgSessionStore(engine=eng, turn_limit=settings.sift_chat_turn_limit),
        persister=persister,
        retriever=_SearchRetriever(settings=settings, engine=eng),
        generator=_EnvAnswerGenerator(),
        rewriter=IdentityRewriter(),
        turn_limit=settings.sift_chat_turn_limit,
        default_top_k=body.top_k,
    )
    checkpointer = await open_postgres_checkpointer()
    graph = build_chat_graph(checkpointer, deps=deps)
    thread = chat_thread_id(session_id)
    qh = query_hash(body.message)
    emit_audit(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action="chat.query",
        target_kind="session",
        target_id=session_id,
        payload={"query_hash": qh, "collection_id": collection_id},
    )

    async def event_stream() -> AsyncIterator[str]:
        cancelled = False
        try:
            if await request.is_disconnected():
                cancelled = True
                return
            result = await graph.ainvoke(
                {
                    "tenant_id": ctx.tenant_id,
                    "collection_id": collection_id,
                    "session_id": session_id,
                    "user_sub": _actor_sub(ctx),
                    "user_message": body.message,
                    "require_review": require_review,
                    "top_k": body.top_k,
                },
                {"configurable": {"thread_id": thread}},
            )
            if await request.is_disconnected():
                cancelled = True
                return
            if result.get("__interrupt__"):
                yield _sse(
                    "done",
                    {
                        "turn_id": None,
                        "insufficient": False,
                        "session_id": session_id,
                        "status": "pending_review",
                    },
                )
                return
            answer = LLMAnswer.model_validate(result.get("answer") or {})
            # One delta with the completed answer — the graph is not a token stream.
            if answer.text:
                yield _sse("token", {"delta": answer.text})
            start = 0
            for cid in answer.cited_chunk_ids:
                end = start + len(cid)
                yield _sse("citation", {"chunk_id": cid, "start": start, "end": end})
                start = end
            yield _sse(
                "usage",
                {"prompt_tokens": 0, "completion_tokens": max(1, len(answer.text) // 4)},
            )
            turn_id = (result.get("persist_turn") or {}).get("turn_id") or persister.last_turn_id
            yield _sse(
                "done",
                {
                    "turn_id": turn_id,
                    "insufficient": bool(result.get("insufficient")),
                    "session_id": session_id,
                    "status": result.get("status"),
                },
            )
            if result.get("needs_summarize"):
                await summarize_session.kiq(session_id, ctx.tenant_id)
            if turn_id:
                await extract_facts.kiq(session_id, ctx.tenant_id, str(turn_id))
        finally:
            if cancelled:
                # Persist cancelled marker via audit only (graph state in checkpointer).
                emit_audit(
                    tenant_id=ctx.tenant_id,
                    actor=ctx.actor,
                    action="chat.query.cancelled",
                    target_kind="session",
                    target_id=session_id,
                    payload={"query_hash": qh},
                )
            eng.dispose()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat/resume")
async def chat_resume(
    body: ChatResumeRequest,
    ctx: Annotated[AuthContext, Depends(require_scopes("chat", "documents:write"))],
) -> dict[str, Any]:
    """Resume a HITL-interrupted chat graph.

    Reviewer must hold ``documents:write`` and must not be the session owner.
    """
    from sift_api.checkpointer import open_postgres_checkpointer

    settings = get_settings()
    eng = _sync_engine(settings)
    try:
        with eng.begin() as conn:
            _with_tenant(conn, ctx.tenant_id)
            row = conn.execute(
                text(
                    """
                    SELECT user_sub FROM chat_sessions
                    WHERE id = :id AND deleted_at IS NULL
                    """
                ),
                {"id": body.session_id},
            ).first()
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="session not found"
                )
            owner = str(row[0])
            if owner == _actor_sub(ctx):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="reviewer must not be the session owner",
                )
        persister = _PgTurnPersister(engine=eng)
        deps = ChatGraphDeps(
            sessions=_PgSessionStore(engine=eng, turn_limit=settings.sift_chat_turn_limit),
            persister=persister,
            retriever=_SearchRetriever(settings=settings, engine=eng),
            generator=_EnvAnswerGenerator(),
            rewriter=IdentityRewriter(),
            turn_limit=settings.sift_chat_turn_limit,
        )
        checkpointer = await open_postgres_checkpointer()
        graph = build_chat_graph(checkpointer, deps=deps)
        decision: dict[str, Any]
        if body.reject:
            decision = {"reject": True, "reason": body.reason or "rejected"}
        else:
            decision = {"approve": True}
            if body.text is not None:
                decision["text"] = body.text
            if body.cited_chunk_ids is not None:
                decision["cited_chunk_ids"] = body.cited_chunk_ids
        result = await graph.ainvoke(
            Command(resume=decision),
            {"configurable": {"thread_id": chat_thread_id(body.session_id)}},
        )
        return {
            "session_id": body.session_id,
            "status": result.get("status"),
            "insufficient": result.get("insufficient"),
            "persist_turn": result.get("persist_turn"),
        }
    finally:
        eng.dispose()


@router.get("/chat/turns/{turn_id}/citations", response_model=list[ChatCitationOut])
async def chat_turn_citations(
    turn_id: str,
    ctx: Annotated[AuthContext, Depends(require_scopes("chat"))],
    session: Annotated[AsyncSession, Depends(tenant_db)],
) -> list[ChatCitationOut]:
    turn = (
        (
            await session.execute(
                text(
                    """
                    SELECT t.cited_chunk_ids
                    FROM chat_turns t
                    JOIN chat_sessions s ON s.id = t.session_id
                    WHERE t.id = :id
                      AND s.user_sub = :user_sub
                      AND s.deleted_at IS NULL
                    """
                ),
                {"id": turn_id, "user_sub": _actor_sub(ctx)},
            )
        )
        .mappings()
        .first()
    )
    if turn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="turn not found")
    chunk_ids = list(turn["cited_chunk_ids"] or [])
    if not chunk_ids:
        return []
    rows = (
        (
            await session.execute(
                text(
                    """
                    SELECT c.id AS chunk_id, c.document_id, c.text_contextualized AS text,
                           c.page_numbers, c.section_path
                    FROM chunks c
                    WHERE c.id = ANY(:ids)
                    """
                ),
                {"ids": chunk_ids},
            )
        )
        .mappings()
        .all()
    )
    by_id = {str(r["chunk_id"]): r for r in rows}
    out: list[ChatCitationOut] = []
    for cid in chunk_ids:
        r = by_id.get(cid)
        if r is None:
            continue
        out.append(
            ChatCitationOut(
                chunk_id=cid,
                document_id=str(r["document_id"]),
                text=r["text"],
                page_numbers=list(r["page_numbers"] or []) or None,
                section_path=list(r["section_path"] or []) or None,
            )
        )
    return out
