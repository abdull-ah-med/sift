"""Chunk quality scorer (absorbed from vendor; light edit for sift_core models)."""

from __future__ import annotations

import logging
import re

from sift_core.chunk import Chunk
from sift_core.models import Block

logger = logging.getLogger(__name__)

_english_words: set[str] | None = None


def _get_english_words() -> set[str]:
    global _english_words
    if _english_words is None:
        _english_words = set()
        try:
            with open("/usr/share/dict/words", encoding="utf-8") as handle:
                _english_words = {line.strip().lower() for line in handle}
        except OSError:
            logger.debug("System dictionary not found; word coverage skipped")
    return _english_words


def _get_lang_confidence(text: str) -> float:
    sample = text.strip().replace("\n", " ")
    if len(sample) < 10:
        return 1.0
    try:
        from fast_langdetect import detect

        from sift_ingest.utils.lang_detect import coerce_detect_result

        _lang, score = coerce_detect_result(detect(sample))
        return score if score > 0.0 else 1.0
    except Exception:
        return 1.0


def score_chunks(chunks: list[Chunk], blocks: list[Block]) -> list[Chunk]:
    """Assign ``quality_score`` on each chunk from block confidence + noise."""
    if not chunks or not blocks:
        return chunks

    block_lookup = {block.id: block for block in blocks}
    scored: list[Chunk] = []
    for chunk in chunks:
        chunk_blocks = [block_lookup[bid] for bid in chunk.block_ids if bid in block_lookup]
        if not chunk_blocks:
            scored.append(chunk.model_copy(update={"quality_score": 0.5}))
            continue

        weighted_sum = sum(
            (b.confidence if b.confidence is not None else 1.0) * len(b.text or "")
            for b in chunk_blocks
        )
        total_weight = sum(len(b.text or "") for b in chunk_blocks)
        base_score = weighted_sum / total_weight if total_weight > 0 else 0.5

        text = chunk.text_raw
        noise_chars = sum(1 for c in text if not (c.isalnum() or c in " .,;:!?()-\"'\n\t"))
        noise_ratio = noise_chars / max(len(text), 1)
        penalty = min(noise_ratio * 2.0, 0.5)

        words = _get_english_words()
        if words:
            tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z]{2,}\b", text)]
            if tokens:
                coverage = sum(1 for t in tokens if t in words) / len(tokens)
                if coverage < 0.6:
                    penalty += min(0.6 - coverage, 0.3)

        lang_score = _get_lang_confidence(text)
        if lang_score < 0.8:
            penalty += (0.8 - lang_score) * 0.5

        ends_properly = text.rstrip().endswith((".", "!", "?", ":", '"'))
        bonus = 0.05 if ends_properly else 0.0
        total_penalty = min(penalty, 0.8)
        final_score = max(0.0, min(1.0, base_score - total_penalty + bonus))
        scored.append(chunk.model_copy(update={"quality_score": final_score}))
    return scored
