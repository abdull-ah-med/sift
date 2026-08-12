"""Chat ask audits query_hash only (unit, mocked graph)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from sift_api.auth import AuthContext
from sift_api.routes import chat as chat_routes
from sift_api.schemas import ChatAskRequest
from sift_api.search import query_hash
from sift_chat.schemas import LLMAnswer


@pytest.mark.asyncio
async def test_chat_ask_audits_query_hash_not_raw_message() -> None:
    audits: list[dict[str, Any]] = []

    def fake_audit(**kwargs: Any) -> None:
        audits.append(kwargs)

    answer = LLMAnswer(
        text="ok",
        cited_chunk_ids=["chunk_1"],
        confidence=0.9,
        insufficient=False,
    )
    graph = MagicMock()
    graph.ainvoke = AsyncMock(
        return_value={
            "answer": answer.model_dump(),
            "insufficient": False,
            "status": "done",
            "needs_summarize": False,
            "persist_turn": {"turn_id": "turn_1"},
        }
    )

    request = MagicMock(spec=Request)
    request.is_disconnected = AsyncMock(return_value=False)
    ctx = AuthContext(
        tenant_id="ten_1",
        actor="key:test",
        scopes=frozenset({"chat"}),
        user_sub="user_1",
    )
    session = AsyncMock()

    with (
        patch.object(chat_routes, "emit_audit", side_effect=fake_audit),
        patch.object(chat_routes, "_ensure_collection", new=AsyncMock()),
        patch.object(chat_routes, "get_settings") as settings_fn,
        patch.object(chat_routes, "_sync_engine") as eng_fn,
        patch.object(chat_routes, "build_chat_graph", return_value=graph),
        patch(
            "sift_api.checkpointer.open_postgres_checkpointer",
            new=AsyncMock(return_value=MagicMock()),
        ),
        patch.object(chat_routes, "_PgSessionStore"),
        patch.object(chat_routes, "_PgTurnPersister") as persister_cls,
        patch.object(chat_routes, "_SearchRetriever"),
        patch.object(chat_routes, "_EnvAnswerGenerator"),
        patch.object(chat_routes, "_require_review_for_collection", return_value=False),
    ):
        settings_fn.return_value = MagicMock(
            sift_chat_turn_limit=12,
            sift_tei_rerank_url="http://localhost",
        )
        eng = MagicMock()
        conn = MagicMock()
        eng.begin.return_value.__enter__.return_value = conn
        eng.begin.return_value.__exit__.return_value = None
        conn.execute.return_value.first.return_value = (1,)
        eng_fn.return_value = eng
        persister_cls.return_value.last_turn_id = "turn_1"

        response = await chat_routes.chat_ask(
            "col_1",
            ChatAskRequest(message="SECRET refund policy", session_id="sess_1"),
            request,
            ctx,
            session,
        )
        chunks: list[str] = []
        async for part in response.body_iterator:
            chunks.append(part if isinstance(part, str) else part.decode())

    body = "".join(chunks)
    assert "event: done" in body
    assert audits
    query_audits = [a for a in audits if a.get("action") == "chat.query"]
    assert len(query_audits) == 1
    payload = query_audits[0]["payload"]
    assert payload["query_hash"] == query_hash("SECRET refund policy")
    assert "SECRET" not in str(payload)
    assert "refund" not in str(payload).lower()


@pytest.mark.asyncio
async def test_chat_ask_withholds_tokens_when_interrupted() -> None:
    audits: list[dict[str, Any]] = []

    def fake_audit(**kwargs: Any) -> None:
        audits.append(kwargs)

    answer = LLMAnswer(
        text="secret answer",
        cited_chunk_ids=["chunk_1"],
        confidence=0.9,
        insufficient=False,
    )
    graph = MagicMock()
    graph.ainvoke = AsyncMock(
        return_value={
            "answer": answer.model_dump(),
            "insufficient": False,
            "status": "validated",
            "needs_summarize": False,
            "persist_turn": None,
            "__interrupt__": [{"type": "chat_answer_review"}],
        }
    )

    request = MagicMock(spec=Request)
    request.is_disconnected = AsyncMock(return_value=False)
    ctx = AuthContext(
        tenant_id="ten_1",
        actor="key:test",
        scopes=frozenset({"chat"}),
        user_sub="user_1",
    )
    session = AsyncMock()

    with (
        patch.object(chat_routes, "emit_audit", side_effect=fake_audit),
        patch.object(chat_routes, "_ensure_collection", new=AsyncMock()),
        patch.object(chat_routes, "get_settings") as settings_fn,
        patch.object(chat_routes, "_sync_engine") as eng_fn,
        patch.object(chat_routes, "build_chat_graph", return_value=graph),
        patch(
            "sift_api.checkpointer.open_postgres_checkpointer",
            new=AsyncMock(return_value=MagicMock()),
        ),
        patch.object(chat_routes, "_PgSessionStore"),
        patch.object(chat_routes, "_PgTurnPersister") as persister_cls,
        patch.object(chat_routes, "_SearchRetriever"),
        patch.object(chat_routes, "_EnvAnswerGenerator"),
        patch.object(chat_routes, "_require_review_for_collection", return_value=True),
    ):
        settings_fn.return_value = MagicMock(
            sift_chat_turn_limit=12,
            sift_tei_rerank_url="http://localhost",
        )
        eng = MagicMock()
        conn = MagicMock()
        eng.begin.return_value.__enter__.return_value = conn
        eng.begin.return_value.__exit__.return_value = None
        conn.execute.return_value.first.return_value = (1,)
        eng_fn.return_value = eng
        persister_cls.return_value.last_turn_id = None

        response = await chat_routes.chat_ask(
            "col_1",
            ChatAskRequest(message="SECRET refund policy", session_id="sess_1"),
            request,
            ctx,
            session,
        )
        chunks: list[str] = []
        async for part in response.body_iterator:
            chunks.append(part if isinstance(part, str) else part.decode())

    body = "".join(chunks)
    assert "event: token" not in body
    assert "secret answer" not in body
    assert "pending_review" in body
    assert "event: done" in body
