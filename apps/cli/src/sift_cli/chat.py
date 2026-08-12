"""Chat CLI helpers (Phase 4 §8)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

import httpx


def parse_sse_chunk(block: str) -> tuple[str | None, dict[str, Any] | None]:
    """Parse one SSE event block into ``(event, data)``."""
    event: str | None = None
    data_raw: str | None = None
    for line in block.splitlines():
        if line.startswith("event:"):
            event = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data_raw = line[len("data:") :].strip()
    if data_raw is None:
        return event, None
    try:
        payload = json.loads(data_raw)
    except json.JSONDecodeError:
        return event, None
    if not isinstance(payload, dict):
        return event, None
    return event, payload


def iter_sse_events(
    chunks: Iterator[str] | list[str],
) -> Iterator[tuple[str | None, dict[str, Any] | None]]:
    """Yield parsed SSE events, including a final unterminated block."""
    buf = ""
    for raw in chunks:
        buf += raw
        while "\n\n" in buf:
            block, buf = buf.split("\n\n", 1)
            yield parse_sse_chunk(block)
    if buf.strip():
        yield parse_sse_chunk(buf)


def chat_ask_payload(message: str, session_id: str | None) -> dict[str, str]:
    """JSON body for ``POST /v1/collections/{id}/chat``."""
    body: dict[str, str] = {"message": message}
    if session_id:
        body["session_id"] = session_id
    return body


def apply_done_event(
    data: dict[str, Any],
    *,
    session_id: str | None,
    cites: list[str],
) -> tuple[str | None, list[str], str | None, bool]:
    """Return ``(session_id, cites, status, insufficient)`` after a ``done`` event."""
    next_session = str(data.get("session_id") or session_id or "") or session_id
    status = str(data.get("status") or "") or None
    insufficient = bool(data.get("insufficient"))
    return next_session, cites, status, insufficient


def stream_chat_turn(
    client: httpx.Client,
    *,
    collection_id: str,
    message: str,
    session_id: str | None,
    on_token: Any,
) -> tuple[list[str], str | None, str | None, bool]:
    """POST one chat turn; return ``(citation_ids, session_id, status, insufficient)``."""
    cites: list[str] = []
    status: str | None = None
    next_session = session_id
    insufficient = False
    with client.stream(
        "POST",
        f"/v1/collections/{collection_id}/chat",
        json=chat_ask_payload(message, session_id),
        timeout=120.0,
    ) as response:
        response.raise_for_status()
        for event, data in iter_sse_events(response.iter_text()):
            if not data:
                continue
            if event == "token":
                on_token(str(data.get("delta") or ""))
            elif event == "citation":
                cid = str(data.get("chunk_id") or "")
                if cid:
                    cites.append(cid)
            elif event == "done":
                next_session, cites, status, insufficient = apply_done_event(
                    data, session_id=next_session, cites=cites
                )
    return cites, next_session, status, insufficient
