"""Cross-reference resolution for chunks (absorbed; sift_core models)."""

from __future__ import annotations

import logging
import re

from sift_core.chunk import Chunk
from sift_core.models import Block, BlockType

logger = logging.getLogger(__name__)

_TARGET_LABEL_RE = re.compile(
    r"((?:Figure|Fig\.|Table|Equation|Eq\.|Section|Sec\.|"
    r"Chart|Diagram|Exhibit|Appendix|App\.)\s*\d+(?:\.\d+)*[a-z]?)",
    re.IGNORECASE,
)
_REFERENCE_RE = re.compile(
    r"(?:see\s+|refer\s+to\s+|shown\s+in\s+|described\s+in\s+|listed\s+in\s+)?"
    r"((?:Figure|Fig\.|Table|Equation|Eq\.|Section|Sec\.|"
    r"Chart|Diagram|Exhibit|Appendix|App\.)\s*\d+(?:\.\d+)*[a-z]?)",
    re.IGNORECASE,
)
_IMPLICIT_FIGURE_RE = re.compile(
    r"\b(?:the\s+)?(?:figure|image|illustration|chart|diagram)\s+"
    r"(?:above|below|following|preceding|previous|next)\b",
    re.IGNORECASE,
)
_IMPLICIT_TABLE_RE = re.compile(
    r"\b(?:the\s+)?(?:table)\s+"
    r"(?:above|below|following|preceding|previous|next)\b",
    re.IGNORECASE,
)
_BEFORE_WORDS = {"above", "preceding", "previous"}
_DIRECTION_RE = re.compile(r"(above|below|following|preceding|previous|next)", re.IGNORECASE)


def _build_proximity_index(blocks: list[Block]) -> dict[str, list[Block]]:
    figures = [b for b in blocks if b.block_type == BlockType.FIGURE]
    tables = [b for b in blocks if b.block_type == BlockType.TABLE]
    return {"figure": figures, "table": tables}


def _find_nearest(
    target_blocks: list[Block],
    anchor_block_ids: list[str],
    all_blocks: list[Block],
    direction: str,
) -> str | None:
    if not target_blocks or not anchor_block_ids:
        return None
    pos_index = {b.id: i for i, b in enumerate(all_blocks)}
    anchor_pos = pos_index.get(anchor_block_ids[0])
    if anchor_pos is None:
        return None
    best_id: str | None = None
    best_distance = float("inf")
    for tb in target_blocks:
        tb_pos = pos_index.get(tb.id)
        if tb_pos is None:
            continue
        if direction == "before" and tb_pos < anchor_pos:
            dist = anchor_pos - tb_pos
            if dist < best_distance:
                best_distance = dist
                best_id = tb.id
        elif direction == "after" and tb_pos > anchor_pos:
            dist = tb_pos - anchor_pos
            if dist < best_distance:
                best_distance = dist
                best_id = tb.id
    return best_id


def resolve_cross_references(
    blocks: list[Block],
    chunks: list[Chunk],
) -> dict[str, list[dict[str, str]]]:
    """Return ``chunk_id -> [{label, target_block_id, ...}]`` links."""
    if not blocks or not chunks:
        return {}

    ref_index: dict[str, str] = {}
    label_types = {
        BlockType.FIGURE,
        BlockType.TABLE,
        BlockType.CAPTION,
        BlockType.FORMULA,
    }
    for block in blocks:
        if block.block_type in label_types and block.text:
            match = _TARGET_LABEL_RE.search(block.text.strip())
            if match:
                ref_index[match.group(1).lower().strip()] = block.id

    prox_index = _build_proximity_index(blocks)
    out: dict[str, list[dict[str, str]]] = {}
    links_added = 0

    for chunk in chunks:
        refs: list[dict[str, str]] = []
        for ref_text in _REFERENCE_RE.findall(chunk.text_raw):
            target_id = ref_index.get(ref_text.lower().strip())
            if target_id and not any(r.get("label") == ref_text for r in refs):
                refs.append({"label": ref_text, "target_block_id": target_id})
                links_added += 1

        for pattern, kind in (
            (_IMPLICIT_FIGURE_RE, "figure"),
            (_IMPLICIT_TABLE_RE, "table"),
        ):
            for match in pattern.finditer(chunk.text_raw):
                phrase = match.group(0)
                dir_match = _DIRECTION_RE.search(phrase)
                if not dir_match:
                    continue
                direction_word = dir_match.group(1).lower()
                direction = "before" if direction_word in _BEFORE_WORDS else "after"
                target_id = _find_nearest(prox_index[kind], chunk.block_ids, blocks, direction)
                if target_id and not any(r.get("target_block_id") == target_id for r in refs):
                    refs.append(
                        {
                            "label": phrase.strip(),
                            "target_block_id": target_id,
                            "resolution": "proximity",
                        }
                    )
                    links_added += 1
        if refs:
            out[chunk.id] = refs

    logger.info("Resolved %d cross-references across %d chunks", links_added, len(chunks))
    return out
