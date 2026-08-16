"""Token-budget context trimming (system > question > chunks > history > summary > facts)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextChunk:
    """Chunk eligible for inclusion in the LLM context window."""

    chunk_id: str
    document_id: str
    text: str
    score: float = 0.0


def estimate_tokens(text: str) -> int:
    """Rough token estimate without a tokenizer dependency (~4 chars/token)."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def budget_trim_context(  # noqa: PLR0913 — context layers are the API
    *,
    system: str,
    question: str,
    chunks: list[ContextChunk],
    history: list[tuple[str, str]],
    rolling_summary: str | None,
    facts: list[str],
    max_tokens: int,
) -> tuple[list[ContextChunk], list[tuple[str, str]], str | None, list[str]]:
    """Trim context by priority: system > question > chunks > history > summary > facts.

    Returns the retained ``(chunks, history, summary, facts)`` that fit under
    ``max_tokens`` together with the immutable system + question overhead.
    """
    reserved = estimate_tokens(system) + estimate_tokens(question)
    remaining = max_tokens - reserved
    if remaining <= 0:
        return [], [], None, []

    kept_chunks: list[ContextChunk] = []
    for chunk in chunks:
        cost = estimate_tokens(chunk.text) + estimate_tokens(chunk.chunk_id) + 8
        if cost > remaining:
            break
        kept_chunks.append(chunk)
        remaining -= cost

    kept_history: list[tuple[str, str]] = []
    # Prefer most recent history turns (append order = chronological).
    for role, text in reversed(history):
        cost = estimate_tokens(role) + estimate_tokens(text) + 2
        if cost > remaining:
            break
        kept_history.append((role, text))
        remaining -= cost
    kept_history.reverse()

    kept_summary = rolling_summary
    if kept_summary:
        cost = estimate_tokens(kept_summary) + 4
        if cost > remaining:
            kept_summary = None
        else:
            remaining -= cost

    kept_facts: list[str] = []
    for fact in facts:
        cost = estimate_tokens(fact) + 2
        if cost > remaining:
            break
        kept_facts.append(fact)
        remaining -= cost

    return kept_chunks, kept_history, kept_summary, kept_facts
