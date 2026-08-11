"""Map vendored ``DoclingDocument`` trees onto product ``ParseResult`` blocks."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from sift_parse_core.types.doc import (
    DocItem,
    DoclingDocument,
    PictureItem,
    SectionHeaderItem,
    TableItem,
    TitleItem,
)
from sift_parse_core.types.doc.base import BoundingBox as DoclingBBox
from sift_parse_core.types.doc.labels import DocItemLabel

from sift.parse.adapter import DocumentMetadata, Page, ParseResult
from sift_core.ids import IdKind, new_id
from sift_core.models import (
    Block,
    BlockType,
    BoundingBox,
    Provenance,
    review_state_for_confidence,
)

_EXTRACTOR = "standard-pdf"
_MODEL_VERSION = "sift-parse-engine"
_DEFAULT_CONFIDENCE = 0.85
_P10_MIN_N = 5
_P10_FRACTION = 0.10


def quality_score_from_confidences(confidences: list[float]) -> float | None:
    """Doc-level quality: p10 when n≥5, else arithmetic mean.

    See ``.sift-local/adr/0016-parse-quality-score.md``.
    """
    if not confidences:
        return None
    values = sorted(c for c in confidences if c is not None)
    if not values:
        return None
    if len(values) >= _P10_MIN_N:
        # Inclusive nearest-rank p10 (1-indexed ranks).
        rank = max(1, round(_P10_FRACTION * len(values)))
        return float(values[rank - 1])
    return float(sum(values) / len(values))


def map_document(
    doc: DoclingDocument,
    *,
    source_path: Path,
    confidence_threshold: float = 0.75,
    page_layout_scores: dict[int, float] | None = None,
) -> ParseResult:
    """Stable pre-order walk → typed ``Block`` list with provenance + hierarchy."""
    page_heights = {page_no: float(page.size.height) for page_no, page in doc.pages.items()}
    page_widths = {page_no: float(page.size.width) for page_no, page in doc.pages.items()}
    page_block_counts: dict[int, int] = dict.fromkeys(doc.pages, 0)
    warnings: list[str] = []
    blocks: list[Block] = []
    ordinal = 0
    scores = page_layout_scores or {}

    for item, _tree_level in doc.iterate_items():
        if not isinstance(item, DocItem):
            continue
        mapped = _map_item(
            item,
            doc=doc,
            ordinal=ordinal,
            confidence_threshold=confidence_threshold,
            page_heights=page_heights,
            page_layout_scores=scores,
            warnings=warnings,
        )
        if mapped is None:
            continue
        blocks.append(mapped)
        page_no = mapped.provenance.page_no
        page_block_counts[page_no] = page_block_counts.get(page_no, 0) + 1
        ordinal += 1

    pages = [
        Page(
            page_no=page_no,
            width=page_widths.get(page_no),
            height=page_heights.get(page_no),
            block_count=page_block_counts.get(page_no, 0),
        )
        for page_no in sorted(doc.pages.keys() or page_block_counts.keys())
    ]
    if not pages and page_block_counts:
        pages = [Page(page_no=p, block_count=c) for p, c in sorted(page_block_counts.items())]

    return ParseResult(
        blocks=blocks,
        metadata=DocumentMetadata(
            source_path=str(source_path.resolve()) if source_path.exists() else str(source_path),
            page_count=len(doc.pages) if doc.pages else len(pages),
            warnings=list(warnings),
        ),
        pages=pages,
        warnings=warnings,
    )


def _map_item(
    item: DocItem,
    *,
    doc: DoclingDocument,
    ordinal: int,
    confidence_threshold: float,
    page_heights: dict[int, float],
    page_layout_scores: dict[int, float],
    warnings: list[str],
) -> Block | None:
    block_type = _block_type_for(item)
    if block_type is None:
        return None
    if not item.prov:
        warnings.append(f"skip {item.self_ref}: missing provenance")
        return None

    prov0 = item.prov[0]
    page_no = int(prov0.page_no)
    bbox = _to_sift_bbox(prov0.bbox, page_heights.get(page_no))
    confidence, conf_note = _resolve_confidence(
        item, page_no=page_no, page_layout_scores=page_layout_scores
    )
    if conf_note:
        warnings.append(f"{item.self_ref}: {conf_note}")

    text = _item_text(item)
    table_data = _table_data(item) if block_type is BlockType.TABLE else None
    figure_data = {"self_ref": item.self_ref} if block_type is BlockType.FIGURE else None
    hierarchy = _section_path(item, doc)

    return Block(
        id=new_id(IdKind.BLOCK),
        ordinal=ordinal,
        block_type=block_type,
        text=text,
        provenance=Provenance(
            page_no=page_no,
            bbox=bbox,
            extractor=_EXTRACTOR,
            model_version=_MODEL_VERSION,
        ),
        confidence=confidence,
        hierarchy=hierarchy or None,
        table_data=table_data,
        figure_data=figure_data,
        review_state=review_state_for_confidence(confidence, threshold=confidence_threshold),
    )


def _block_type_for(item: DocItem) -> BlockType | None:
    if isinstance(item, TitleItem | SectionHeaderItem):
        return BlockType.HEADING
    if isinstance(item, TableItem):
        return BlockType.TABLE
    if isinstance(item, PictureItem):
        return BlockType.FIGURE
    label = getattr(item, "label", None)
    if label is DocItemLabel.CAPTION:
        return BlockType.CAPTION
    if label is DocItemLabel.FOOTNOTE:
        return BlockType.FOOTNOTE
    if label is DocItemLabel.LIST_ITEM:
        return BlockType.LIST_ITEM
    if label in {
        DocItemLabel.PARAGRAPH,
        DocItemLabel.TEXT,
        DocItemLabel.PAGE_HEADER,
        DocItemLabel.PAGE_FOOTER,
        DocItemLabel.REFERENCE,
    }:
        return BlockType.PARAGRAPH
    if label is DocItemLabel.CODE:
        return BlockType.CODE
    if label is DocItemLabel.FORMULA:
        return BlockType.FORMULA
    return None


def _item_text(item: DocItem) -> str | None:
    text = getattr(item, "text", None)
    if isinstance(text, str) and text.strip():
        return text
    if isinstance(item, TableItem):
        cells = [c.text for c in item.data.table_cells if c.text]
        return "\n".join(cells) if cells else None
    if isinstance(item, PictureItem):
        return None
    return text if isinstance(text, str) else None


def _table_data(item: DocItem) -> dict[str, Any] | None:
    if not isinstance(item, TableItem):
        return None
    data = item.data
    return {
        "num_rows": data.num_rows,
        "num_cols": data.num_cols,
        "cells": [
            {
                "text": cell.text,
                "row": cell.start_row_offset_idx,
                "col": cell.start_col_offset_idx,
                "row_span": cell.row_span,
                "col_span": cell.col_span,
            }
            for cell in data.table_cells
        ],
    }


def _section_path(item: DocItem, doc: DoclingDocument) -> list[str]:
    path: list[str] = []
    parent_ref = item.parent
    while parent_ref is not None:
        try:
            parent = parent_ref.resolve(doc)
        except Exception:
            break
        if isinstance(parent, TitleItem | SectionHeaderItem):
            path.append(parent.text)
        parent_ref = getattr(parent, "parent", None)
    path.reverse()
    return path


def _to_sift_bbox(bbox: DoclingBBox, page_height: float | None) -> BoundingBox:
    converted = bbox.to_bottom_left_origin(page_height) if page_height is not None else bbox
    y0 = float(min(converted.b, converted.t))
    y1 = float(max(converted.b, converted.t))
    return BoundingBox(x0=float(converted.l), y0=y0, x1=float(converted.r), y1=y1)


def _resolve_confidence(
    item: DocItem,
    *,
    page_no: int,
    page_layout_scores: dict[int, float],
) -> tuple[float, str | None]:
    meta = item.meta
    if meta is not None:
        for field_name in (
            "classification",
            "summary",
            "description",
            "language",
        ):
            field = getattr(meta, field_name, None)
            conf = getattr(field, "confidence", None) if field is not None else None
            if conf is not None:
                return float(conf), None
        extra = meta.get_custom_part()
        if "sift__confidence" in extra:
            return float(extra["sift__confidence"]), None

    layout = page_layout_scores.get(page_no)
    if layout is not None and math.isfinite(layout):
        return float(layout), None

    return _DEFAULT_CONFIDENCE, f"missing confidence; defaulted to {_DEFAULT_CONFIDENCE}"
