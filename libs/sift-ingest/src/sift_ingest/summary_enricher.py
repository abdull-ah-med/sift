"""Section summary helpers that feed contextual prefixes (Phase 2 §5)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

type SectionKey = tuple[str, ...]
type LlmSummarize = Callable[[str], Awaitable[str]]


async def generate_section_summaries(
    sections: dict[SectionKey, str],
    *,
    summarize: LlmSummarize,
    max_chars: int = 8000,
) -> dict[SectionKey, str]:
    """Summarize each section's concatenated text via the provided LLM callable.

    Unlike the vendor Motor-backed enricher, this is storage-agnostic so
    ``contextual_prefix`` / Taskiq workers can supply their own I/O.
    """
    out: dict[SectionKey, str] = {}
    for key, text in sections.items():
        clipped = text if len(text) <= max_chars else text[:max_chars] + "..."
        if not clipped.strip():
            continue
        try:
            out[key] = (await summarize(clipped)).strip()
        except Exception:
            logger.exception("summary_enricher failed section=%s", "/".join(key))
    return out


def group_texts_by_section(paths: list[list[str]], texts: list[str]) -> dict[SectionKey, str]:
    """Group raw texts by section path for summary enrichment."""
    groups: dict[SectionKey, list[str]] = {}
    for path, text in zip(paths, texts, strict=True):
        key = tuple(path) if path else ("",)
        groups.setdefault(key, []).append(text)
    return {key: "\n\n".join(parts) for key, parts in groups.items()}
