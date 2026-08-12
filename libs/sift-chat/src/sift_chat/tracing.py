"""Tracing hooks for chat graph nodes (OTel + optional Langfuse)."""

from __future__ import annotations

import time
from collections.abc import Callable
from contextlib import nullcontext
from typing import Any

from opentelemetry import trace

try:
    from sift_obs.chat_metrics import record_insufficient, record_phase_latency
    from sift_obs.langfuse_chat import chat_turn_trace
    from sift_obs.langfuse_chat import span as langfuse_span
except ImportError:  # pragma: no cover - obs optional at import time in isolation

    def record_phase_latency(*, phase: str, latency_ms: float) -> None:
        _ = phase, latency_ms

    def record_insufficient(*, collection_id: str) -> None:
        _ = collection_id

    def chat_turn_trace(**_kwargs: Any) -> Any:
        return nullcontext(None)

    def langfuse_span(
        trace_obj: Any,
        *,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        _ = trace_obj, name, metadata
        return None


_tracer = trace.get_tracer("sift.chat")

_PHASE_BY_NODE = {
    "retrieve_hybrid": "retrieve",
    "rerank": "rerank",
    "generate_structured": "generate",
    "validate_citations": "validate",
}


def timed_node[T](node_name: str, fn: Callable[[T], T]) -> Callable[[T], T]:
    """Wrap a graph node to emit OTel span + phase latency histogram."""

    def _wrapped(state: T) -> T:
        phase = _PHASE_BY_NODE.get(node_name, node_name)
        started = time.perf_counter()
        with _tracer.start_as_current_span(f"chat.{node_name}"):
            out = fn(state)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        record_phase_latency(phase=phase, latency_ms=elapsed_ms)
        if (
            node_name == "validate_citations"
            and isinstance(out, dict)
            and out.get("insufficient")
        ):
            record_insufficient(collection_id=str(out.get("collection_id") or "unknown"))
        return out

    return _wrapped


__all__ = [
    "chat_turn_trace",
    "langfuse_span",
    "record_insufficient",
    "record_phase_latency",
    "timed_node",
]
