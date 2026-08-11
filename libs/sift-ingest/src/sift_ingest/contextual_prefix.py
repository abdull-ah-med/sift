"""Anthropic-style contextual prefix for chunks (Phase 2 §3 step 5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sift_core.chunk import Chunk


@dataclass(frozen=True, slots=True)
class PrefixCostRecord:
    """Per-document prefix cost for Langfuse / exit-gate assertions."""

    total_usd: float
    chunk_count: int


class PrefixGenerator(Protocol):
    """Small LLM that situates a chunk inside its parent document."""

    def generate(self, *, document_text: str, chunk_text: str) -> tuple[str, float]:
        """Return ``(prefix_text, cost_usd)`` for one chunk."""
        ...


def apply_contextual_prefixes(
    chunks: list[Chunk],
    *,
    document_text: str,
    generator: PrefixGenerator,
    cost_log: list[PrefixCostRecord] | None = None,
) -> list[Chunk]:
    """Prepend LLM situating context so ``text_contextualized ≠ text_raw``.

    TDD stub — real Anthropic-style prompt lands in the impl commit.
    """
    del document_text, generator, cost_log
    return list(chunks)
