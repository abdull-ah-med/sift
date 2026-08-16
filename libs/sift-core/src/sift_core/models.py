"""Domain models shared across sift services (Phase 2+)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BlockType(StrEnum):
    """Canonical block kinds persisted in ``blocks.block_type``."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    CODE = "code"
    LIST_ITEM = "list_item"
    CAPTION = "caption"
    FOOTNOTE = "footnote"


class ReviewState(StrEnum):
    """HITL review states for blocks (``02-data-model.md`` §4.7)."""

    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    CONFLICT = "conflict"


class ChatRole(StrEnum):
    """Roles persisted in ``chat_turns.role`` (``02-data-model.md`` §4.16)."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class BoundingBox(BaseModel):
    """PDF-space bounding box."""

    model_config = ConfigDict(extra="forbid", strict=True)

    x0: float
    y0: float
    x1: float
    y1: float


class Provenance(BaseModel):
    """Traceability for a parsed block."""

    model_config = ConfigDict(extra="forbid", strict=True)

    page_no: int = Field(ge=1)
    bbox: BoundingBox
    extractor: str
    model_version: str


class Block(BaseModel):
    """Document element ready for Postgres ``blocks`` persistence."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    ordinal: int = Field(ge=0)
    block_type: BlockType
    text: str | None = None
    html: str | None = None
    provenance: Provenance
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    hierarchy: list[str] | None = None
    cross_refs: list[str] = Field(default_factory=list)
    table_data: dict[str, object] | None = None
    figure_data: dict[str, object] | None = None
    formula_data: dict[str, object] | None = None
    pii_map: dict[str, object] | None = None
    review_state: ReviewState = ReviewState.PENDING
    version: int = Field(default=1, ge=1)


class LongTermFact(BaseModel):
    """Durable fact extracted from chat answers (``chat_sessions.long_term_facts``)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    text: str
    source_chunk_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class ChatSession(BaseModel):
    """Collection-scoped chat session row (``02-data-model.md`` §4.16)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    tenant_id: str
    collection_id: str
    user_sub: str
    title: str | None = None
    rolling_summary: str | None = None
    long_term_facts: list[LongTermFact] = Field(default_factory=list)
    created_at: datetime | None = None
    last_message_at: datetime | None = None
    deleted_at: datetime | None = None


class ChatTurn(BaseModel):
    """Single turn within a chat session (``02-data-model.md`` §4.16)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    session_id: str
    role: ChatRole
    content: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    cited_documents: list[str] = Field(default_factory=list)
    usage: dict[str, Any] | None = None
    latency_ms: int | None = None
    langfuse_trace_id: str | None = None
    created_at: datetime | None = None


def review_state_for_confidence(
    confidence: float,
    *,
    threshold: float = 0.75,
) -> ReviewState:
    """Map extraction confidence to initial review state."""
    if confidence < threshold:
        return ReviewState.NEEDS_REVIEW
    return ReviewState.APPROVED
