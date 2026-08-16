"""Chat turn metrics (Phase 4 §9)."""

from __future__ import annotations

from opentelemetry import metrics

_meter = metrics.get_meter("sift.chat")

turn_latency = _meter.create_histogram(
    name="sift_chat_turn_latency",
    unit="ms",
    description="Chat turn latency by graph phase",
)

insufficient_total = _meter.create_counter(
    name="sift_chat_insufficient_total",
    description="Chat turns marked insufficient (by collection id hash bucket)",
)


def record_phase_latency(*, phase: str, latency_ms: float) -> None:
    """Record latency for a chat graph phase (retrieve / rerank / generate / validate)."""
    turn_latency.record(latency_ms, {"phase": phase})


def record_insufficient(*, collection_id: str) -> None:
    """Increment insufficient counter (label is collection id, not raw query)."""
    insufficient_total.add(1, {"collection": collection_id})
