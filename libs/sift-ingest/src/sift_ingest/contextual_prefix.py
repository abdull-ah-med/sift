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
    """Prepend LLM situating context so ``text_contextualized ≠ text_raw``."""
    if not chunks:
        if cost_log is not None:
            cost_log.append(PrefixCostRecord(total_usd=0.0, chunk_count=0))
        return []

    total_usd = 0.0
    out: list[Chunk] = []
    for chunk in chunks:
        prefix, cost = generator.generate(
            document_text=document_text,
            chunk_text=chunk.text_raw,
        )
        total_usd += float(cost)
        contextualized = f"{prefix.strip()}\n\n{chunk.text_raw}"
        out.append(
            chunk.model_copy(
                update={
                    "text_contextualized": contextualized,
                    "token_count": max(1, len(contextualized.split())),
                }
            )
        )
    if cost_log is not None:
        cost_log.append(PrefixCostRecord(total_usd=total_usd, chunk_count=len(out)))
    return out
