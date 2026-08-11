"""Domain models shared across sift services (Phase 2+)."""

from __future__ import annotations

from enum import StrEnum

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


def review_state_for_confidence(
    confidence: float,
    *,
    threshold: float = 0.75,
) -> ReviewState:
    """Map extraction confidence to initial review state."""
    if confidence < threshold:
        return ReviewState.NEEDS_REVIEW
    return ReviewState.APPROVED
