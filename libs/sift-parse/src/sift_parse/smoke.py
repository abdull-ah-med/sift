"""Phase 0 parse smoke: convert one PDF via the vendored pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


class ParseSmokeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    blocks: int = Field(ge=0)
    markdown_length: int = Field(ge=0)
    source: str


class SupportsConvert(Protocol):
    def convert(self, source: str | Path) -> object: ...


ConverterFactory = Callable[[], SupportsConvert]


def _default_converter() -> SupportsConvert:
    """Build DocumentConverter from the vendored Docling tree.

    Raises ImportError when heavy parse deps are not installed in this env.
    """
    try:
        from docling.document_converter import DocumentConverter  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - optional heavy dep
        raise ImportError(
            "vendored sift-parse runtime not installed; install vendor extras"
        ) from exc

    converter: SupportsConvert = DocumentConverter()
    return converter


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


def run_parse_smoke(
    path: Path,
    *,
    converter_factory: ConverterFactory | None = None,
) -> ParseSmokeResult:
    """Run StandardPdf-class conversion on ``path`` and return block counts.

    ``converter_factory`` is injectible so unit tests never load model weights.
    """
    if not path.is_file():
        raise FileNotFoundError(path)

    factory = converter_factory or _default_converter
    converter = factory()
    result = converter.convert(path)
    document = getattr(result, "document", result)
    return ParseSmokeResult(
        blocks=_count_blocks(document),
        markdown_length=_markdown_length(document),
        source=str(path.resolve()),
    )
