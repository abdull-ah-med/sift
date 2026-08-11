"""Chunk domain model (Phase 2; embeddings arrive in Phase 3)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ChunkType(StrEnum):
    PROSE = "prose"
    TABLE = "table"
    CODE = "code"
    FORMULA = "formula"
    FIGURE_CAPTION = "figure_caption"
    SUMMARY = "summary"


class Chunk(BaseModel):
    """Chunk ready for Postgres ``chunks`` persistence (unembedded)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    id: str
    ordinal: int = Field(ge=0)
    text_raw: str
    text_contextualized: str
    token_count: int = Field(ge=0)
    chunk_type: ChunkType = ChunkType.PROSE
    section_path: list[str] = Field(default_factory=list)
    page_numbers: list[int] = Field(default_factory=list)
    block_ids: list[str] = Field(default_factory=list)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
