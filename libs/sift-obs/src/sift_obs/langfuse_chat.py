"""Optional Langfuse tracing for chat turns (no-op without credentials)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


@contextmanager
def chat_turn_trace(
    *,
    session_id: str,
    collection_id: str,
    turn_name: str = "chat.turn",
) -> Iterator[Any]:
    """Open a Langfuse trace when keys are present; otherwise yield ``None``.

    Never logs raw user messages — only ids.
    """
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
    if not public_key or not secret_key:
        yield None
        return
    try:
        from langfuse import Langfuse  # noqa: PLC0415 — optional dep
    except ImportError:
        yield None
        return

    client = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )
    trace = client.trace(
        name=turn_name,
        session_id=session_id,
        metadata={"collection_id": collection_id},
    )
    try:
        yield trace
    finally:
        client.flush()


def span(trace: Any, *, name: str, metadata: dict[str, Any] | None = None) -> Any:
    """Start a nested Langfuse span when ``trace`` is live."""
    if trace is None:
        return None
    return trace.span(name=name, metadata=metadata or {})
