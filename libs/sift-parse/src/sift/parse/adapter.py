"""Product-facing parse adapter over digital / vendored engines.

Phase 2 contract from ``05-phase-2-intelligence.md`` §2.1. Heavy vendored
``StandardPdfPipeline`` wiring lands behind the same ``Parser`` protocol;
digital PDF extraction ships first so ingest can persist blocks without
layout-model downloads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from sift_core.models import Block


class ParseConfig(BaseModel):
    """Runtime knobs for a single parse invocation."""

    model_config = ConfigDict(extra="forbid", strict=True)

    allow_url_fetch: bool = False
    confidence_threshold: float = Field(default=0.75, ge=0.0)
    ocr_default_lang: str = "eng"


class DocumentMetadata(BaseModel):
    """Document-level parse metadata."""

    model_config = ConfigDict(extra="forbid", strict=True)

    source_path: str
    page_count: int = Field(ge=0)
    language: str | None = None
    warnings: list[str] = Field(default_factory=list)


class Page(BaseModel):
    """Per-page summary from a parse."""

    model_config = ConfigDict(extra="forbid", strict=True)

    page_no: int = Field(ge=1)
    width: float | None = None
    height: float | None = None
    block_count: int = Field(ge=0)


class ParseResult(BaseModel):
    """Normalized parse output consumed by ingest / HITL."""

    model_config = ConfigDict(extra="forbid", strict=True)

    blocks: list[Block]
    metadata: DocumentMetadata
    pages: list[Page]
    warnings: list[str] = Field(default_factory=list)


class Parser(Protocol):
    """Stable seam: path + config → ordered blocks with provenance."""

    def parse(self, path: Path, config: ParseConfig) -> ParseResult: ...
