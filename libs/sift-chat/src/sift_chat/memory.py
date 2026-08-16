"""Three-layer session memory helpers (turns + rolling summary + facts)."""

from __future__ import annotations

from collections.abc import Sequence

from sift_core.models import LongTermFact

DEFAULT_TURN_LIMIT = 12
_SUMMARY_SNIPPET_CHARS = 500
_MIN_FACT_CHARS = 12


def turns_for_verbatim_window(
    turns: Sequence[dict[str, object]],
    *,
    limit: int = DEFAULT_TURN_LIMIT,
) -> list[dict[str, object]]:
    """Return the most recent ``limit`` turns to keep verbatim in the graph."""
    if limit <= 0:
        return []
    return [dict(t) for t in list(turns)[-limit:]]


def turns_needing_summary(
    turns: Sequence[dict[str, object]],
    *,
    limit: int = DEFAULT_TURN_LIMIT,
) -> list[dict[str, object]]:
    """Return older turns past the verbatim window (candidates for condensation)."""
    rows = list(turns)
    if len(rows) <= limit:
        return []
    return [dict(t) for t in rows[:-limit]]


def should_summarize(
    turn_count: int,
    *,
    limit: int = DEFAULT_TURN_LIMIT,
) -> bool:
    """True when turn count exceeds the verbatim window."""
    return turn_count > limit


def condense_turns_extractive(turns: Sequence[dict[str, object]]) -> str:
    """Deterministic condensation of older turns (no LLM required).

    Used by the background task when an LLM summarizer is not configured;
    preserves role-tagged content in chronological order for the rolling summary.
    """
    lines: list[str] = []
    for turn in turns:
        role = str(turn.get("role") or "user")
        content = str(turn.get("content") or "").strip()
        if not content:
            continue
        # Keep summaries bounded; full text remains in chat_turns rows.
        snippet = (
            content
            if len(content) <= _SUMMARY_SNIPPET_CHARS
            else f"{content[: _SUMMARY_SNIPPET_CHARS - 3]}..."
        )
        lines.append(f"{role}: {snippet}")
    return "\n".join(lines)


def merge_rolling_summary(existing: str | None, addition: str) -> str:
    """Append a new condensation block onto the rolling summary."""
    addition = addition.strip()
    if not addition:
        return (existing or "").strip()
    if not existing or not existing.strip():
        return addition
    return f"{existing.strip()}\n---\n{addition}"


def dedupe_facts(facts: Sequence[LongTermFact | dict[str, object]]) -> list[LongTermFact]:
    """Deduplicate facts by normalized text + source_chunk_id."""
    seen: set[tuple[str, str | None]] = set()
    out: list[LongTermFact] = []
    for item in facts:
        fact = item if isinstance(item, LongTermFact) else LongTermFact.model_validate(item)
        key = (fact.text.strip().lower(), fact.source_chunk_id)
        if key in seen or not fact.text.strip():
            continue
        seen.add(key)
        out.append(fact)
    return out


def extract_facts_from_answer(
    *,
    answer_text: str,
    cited_chunk_ids: Sequence[str],
    confidence: float,
) -> list[LongTermFact]:
    """Pull durable fact candidates from a grounded assistant answer.

    Heuristic BUILD path: one fact per non-empty sentence when citations exist.
    HARDEN may replace with an LLM extractor behind the same Taskiq task.
    """
    if not cited_chunk_ids or not answer_text.strip():
        return []
    source = cited_chunk_ids[0]
    sentences = [
        part.strip()
        for part in answer_text.replace("!", ".").replace("?", ".").split(".")
        if part.strip()
    ]
    facts = [
        LongTermFact(text=sentence, source_chunk_id=source, confidence=confidence)
        for sentence in sentences
        if len(sentence) >= _MIN_FACT_CHARS
    ]
    return dedupe_facts(facts)
