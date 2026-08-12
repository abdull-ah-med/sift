"""Observability helpers for sift (OTel + structlog)."""

from __future__ import annotations

import logging

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from sift_obs.chat_metrics import record_insufficient, record_phase_latency
from sift_obs.langfuse_chat import chat_turn_trace
from sift_obs.langfuse_chat import span as langfuse_span

__all__ = [
    "chat_turn_trace",
    "get_logger",
    "langfuse_span",
    "record_insufficient",
    "record_phase_latency",
    "setup_logging",
    "setup_tracing",
]


def setup_tracing(*, service_name: str, otlp_endpoint: str) -> None:
    """Configure a TracerProvider exporting OTLP/HTTP to Tempo (or compatible)."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def setup_logging(*, json_logs: bool = True) -> None:
    """Configure structlog for consistent service logs."""
    shared = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    if json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()
    structlog.configure(
        processors=[*shared, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
