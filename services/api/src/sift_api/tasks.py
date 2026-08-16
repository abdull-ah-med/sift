"""Taskiq broker wiring."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from sift_api.db import sync_dsn
from sift_api.embed import run_embed_document
from sift_api.ingest import run_ingest_document
from sift_api.settings import Settings, get_settings
from sift_chat.memory import (
    condense_turns_extractive,
    dedupe_facts,
    extract_facts_from_answer,
    merge_rolling_summary,
    should_summarize,
    turns_needing_summary,
)
from sift_core.db import tenant_guc_statements
from sift_core.models import LongTermFact

_settings = get_settings()
broker = RedisStreamBroker(url=_settings.sift_valkey_url).with_result_backend(
    RedisAsyncResultBackend(redis_url=_settings.sift_valkey_url)
)


@broker.task(task_name="ingest_document")
async def ingest_document(document_id: str, job_id: str, tenant_id: str) -> None:
    run_ingest_document(document_id=document_id, job_id=job_id, tenant_id=tenant_id)


@broker.task(task_name="embed_document")
async def embed_document(
    document_id: str,
    tenant_id: str,
    force: bool = False,
) -> None:
    """Embed approved chunks for a finalized document (dense-only; ADR-0021)."""
    run_embed_document(document_id=document_id, tenant_id=tenant_id, force=force)


def _engine(settings: Settings) -> Engine:
    return create_engine(sync_dsn(settings), pool_pre_ping=True)


def _apply_tenant(conn: Connection, tenant_id: str) -> None:
    for statement in tenant_guc_statements(tenant_id):
        conn.execute(text(statement))


def _load_session_turns(
    conn: Connection,
    *,
    session_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    session = (
        conn.execute(
            text(
                """
                SELECT id, tenant_id, rolling_summary, long_term_facts
                FROM chat_sessions
                WHERE id = :session_id AND deleted_at IS NULL
                """
            ),
            {"session_id": session_id},
        )
        .mappings()
        .first()
    )
    if session is None:
        msg = f"chat session not found: {session_id}"
        raise ValueError(msg)
    turns = [
        dict(row)
        for row in conn.execute(
            text(
                """
                SELECT id, role, content, cited_chunk_ids, created_at
                FROM chat_turns
                WHERE session_id = :session_id
                ORDER BY created_at ASC
                """
            ),
            {"session_id": session_id},
        ).mappings()
    ]
    return dict(session), turns


def run_summarize_session(
    *,
    session_id: str,
    tenant_id: str,
    settings: Settings | None = None,
    engine: Engine | None = None,
) -> None:
    """Refresh ``chat_sessions.rolling_summary`` from turns past the verbatim window."""
    cfg = settings or get_settings()
    if not cfg.sift_chat_memory_enabled:
        return
    limit = cfg.sift_chat_turn_limit
    eng = engine or _engine(cfg)
    with eng.begin() as conn:
        _apply_tenant(conn, tenant_id)
        session, turns = _load_session_turns(conn, session_id=session_id)
        if not should_summarize(len(turns), limit=limit):
            return
        older = turns_needing_summary(turns, limit=limit)
        addition = condense_turns_extractive(older)
        merged = merge_rolling_summary(session.get("rolling_summary"), addition)
        conn.execute(
            text(
                """
                UPDATE chat_sessions
                SET rolling_summary = :rolling_summary
                WHERE id = :session_id AND tenant_id = :tenant_id
                """
            ),
            {
                "rolling_summary": merged,
                "session_id": session_id,
                "tenant_id": tenant_id,
            },
        )


def run_extract_facts(
    *,
    session_id: str,
    tenant_id: str,
    turn_id: str,
    settings: Settings | None = None,
    engine: Engine | None = None,
) -> None:
    """Merge durable facts from an assistant turn into ``long_term_facts``."""
    cfg = settings or get_settings()
    if not cfg.sift_chat_memory_enabled:
        return
    eng = engine or _engine(cfg)
    with eng.begin() as conn:
        _apply_tenant(conn, tenant_id)
        session, _turns = _load_session_turns(conn, session_id=session_id)
        turn = (
            conn.execute(
                text(
                    """
                    SELECT id, role, content, cited_chunk_ids
                    FROM chat_turns
                    WHERE id = :turn_id AND session_id = :session_id
                    """
                ),
                {"turn_id": turn_id, "session_id": session_id},
            )
            .mappings()
            .first()
        )
        if turn is None or str(turn.get("role")) != "assistant":
            return
        cited = list(turn.get("cited_chunk_ids") or [])
        new_facts = extract_facts_from_answer(
            answer_text=str(turn.get("content") or ""),
            cited_chunk_ids=[str(c) for c in cited],
            confidence=0.7,
        )
        existing_raw = session.get("long_term_facts") or []
        if isinstance(existing_raw, str):
            existing_raw = json.loads(existing_raw)
        existing = [
            LongTermFact.model_validate(item) if not isinstance(item, LongTermFact) else item
            for item in existing_raw
        ]
        merged = dedupe_facts([*existing, *new_facts])
        payload = [f.model_dump() for f in merged]
        conn.execute(
            text(
                """
                UPDATE chat_sessions
                SET long_term_facts = CAST(:facts AS jsonb)
                WHERE id = :session_id AND tenant_id = :tenant_id
                """
            ),
            {
                "facts": json.dumps(payload),
                "session_id": session_id,
                "tenant_id": tenant_id,
            },
        )


@broker.task(task_name="summarize_session")
async def summarize_session(session_id: str, tenant_id: str) -> None:
    """Background rolling-summary update after chat turns exceed the window."""
    run_summarize_session(session_id=session_id, tenant_id=tenant_id)


@broker.task(task_name="extract_facts")
async def extract_facts(session_id: str, tenant_id: str, turn_id: str) -> None:
    """Background long-term fact extraction from a persisted assistant turn."""
    run_extract_facts(session_id=session_id, tenant_id=tenant_id, turn_id=turn_id)
