"""Structured LLM answer schema for collection-scoped RAG."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LLMAnswer(BaseModel):
    """Instructor response model for grounded chat answers."""

    model_config = ConfigDict(extra="forbid", strict=True)

    text: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    insufficient: bool = False
