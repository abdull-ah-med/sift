"""Phase 0 parse smoke: digital PDF extraction with optional vendored engine path."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import pypdfium2 as pdfium  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field


class ParseSmokeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    blocks: int = Field(ge=0)
    markdown_length: int = Field(ge=0)
    source: str
    engine: str = "pypdfium2"


class SupportsConvert(Protocol):
    def convert(self, source: str | Path) -> object: ...


ConverterFactory = Callable[[], SupportsConvert]


def _count_blocks(document: object) -> int:
    texts = getattr(document, "texts", None)
    tables = getattr(document, "tables", None)
    pictures = getattr(document, "pictures", None)
    count = 0
    for collection in (texts, tables, pictures):
        if collection is None:
            continue
        try:
            count += len(collection)
        except TypeError:
            continue
    if count == 0:
        iterate = getattr(document, "iterate_items", None)
        if callable(iterate):
            count = sum(1 for _ in iterate())
    return count


def _markdown_length(document: object) -> int:
    export = getattr(document, "export_to_markdown", None)
    if not callable(export):
        return 0
    markdown = export()
    if not isinstance(markdown, str):
        return 0
    return len(markdown)


def _digital_pdf_smoke(path: Path) -> ParseSmokeResult:
    """Extract page text blocks via pypdfium2 (Phase 0 digital-PDF gate)."""
    document = pdfium.PdfDocument(str(path))
    blocks: list[str] = []
    for page_index in range(len(document)):
        page = document[page_index]
        textpage = page.get_textpage()
        text = textpage.get_text_bounded().strip()
        textpage.close()
        page.close()
        if text:
            blocks.append(text)
    document.close()
    markdown = "\n\n".join(blocks)
    return ParseSmokeResult(
        blocks=len(blocks),
        markdown_length=len(markdown),
        source=str(path.resolve()),
        engine="pypdfium2",
    )


def _vendored_converter() -> SupportsConvert:
    try:
        from sift_parse.document_converter import (
            DocumentConverter,
        )
    except ImportError as exc:  # pragma: no cover - optional heavy dep
        raise ImportError(
            "vendored sift-parse runtime not installed; install vendor extras"
        ) from exc
    converter: SupportsConvert = DocumentConverter()
    return converter


def run_parse_smoke(
    path: Path,
    *,
    converter_factory: ConverterFactory | None = None,
) -> ParseSmokeResult:
    """Return block counts for ``path``.

    Default Phase 0 engine is pypdfium2 digital extraction (meets exit gate without
    downloading layout models). Set ``SIFT_PARSE_ENGINE=sift-parse`` (or pass
    ``converter_factory``) to exercise the vendored StandardPdfPipeline path.
    Deprecated alias: ``SIFT_PARSE_ENGINE=docling`` (removed after Phase 2).
    """
    if not path.is_file():
        raise FileNotFoundError(path)

    if converter_factory is not None:
        converter = converter_factory()
        result = converter.convert(path)
        document = getattr(result, "document", result)
        return ParseSmokeResult(
            blocks=_count_blocks(document),
            markdown_length=_markdown_length(document),
            source=str(path.resolve()),
            engine="injected",
        )

    engine = os.environ.get("SIFT_PARSE_ENGINE", "pypdfium2").lower()
    if engine in {"sift-parse", "standard", "docling"}:
        converter = _vendored_converter()
        result = converter.convert(path)
        document = getattr(result, "document", result)
        return ParseSmokeResult(
            blocks=_count_blocks(document),
            markdown_length=_markdown_length(document),
            source=str(path.resolve()),
            engine="sift-parse",
        )

    return _digital_pdf_smoke(path)
