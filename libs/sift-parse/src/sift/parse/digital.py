"""Digital PDF parser via pypdfium2 (no layout-model download)."""

from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium  # type: ignore[import-untyped]

from sift.parse.adapter import DocumentMetadata, Page, ParseConfig, ParseResult
from sift_core.ids import IdKind, new_id
from sift_core.models import (
    Block,
    BlockType,
    BoundingBox,
    Provenance,
    review_state_for_confidence,
)

_EXTRACTOR = "digital-pdf"
_MODEL_VERSION = "pypdfium2"


class DigitalPdfParser:
    """Extract page text blocks for digital (non-scanned) PDFs."""

    def parse(self, path: Path, config: ParseConfig) -> ParseResult:
        if not path.is_file():
            raise FileNotFoundError(path)
        if config.allow_url_fetch:
            # Remote fetch stays off until collection policy opts in (Phase 2 §2.2).
            raise ValueError("allow_url_fetch is not supported by DigitalPdfParser")

        document = pdfium.PdfDocument(str(path))
        blocks: list[Block] = []
        pages: list[Page] = []
        warnings: list[str] = []
        ordinal = 0

        try:
            page_count = len(document)
            for page_index in range(page_count):
                page = document[page_index]
                try:
                    width, height = page.get_size()
                    textpage = page.get_textpage()
                    try:
                        text = textpage.get_text_bounded().strip()
                    finally:
                        textpage.close()
                finally:
                    page.close()

                page_no = page_index + 1
                page_blocks = 0
                if text:
                    confidence = 0.99
                    block = Block(
                        id=new_id(IdKind.BLOCK),
                        ordinal=ordinal,
                        block_type=BlockType.PARAGRAPH,
                        text=text,
                        provenance=Provenance(
                            page_no=page_no,
                            bbox=BoundingBox(x0=0.0, y0=0.0, x1=float(width), y1=float(height)),
                            extractor=_EXTRACTOR,
                            model_version=_MODEL_VERSION,
                        ),
                        confidence=confidence,
                        review_state=review_state_for_confidence(
                            confidence,
                            threshold=config.confidence_threshold,
                        ),
                    )
                    blocks.append(block)
                    ordinal += 1
                    page_blocks = 1
                else:
                    warnings.append(f"page {page_no}: no extractable text")

                pages.append(
                    Page(
                        page_no=page_no,
                        width=float(width),
                        height=float(height),
                        block_count=page_blocks,
                    )
                )
        finally:
            document.close()

        return ParseResult(
            blocks=blocks,
            metadata=DocumentMetadata(
                source_path=str(path.resolve()),
                page_count=page_count,
                warnings=list(warnings),
            ),
            pages=pages,
            warnings=warnings,
        )
