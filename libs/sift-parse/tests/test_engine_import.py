"""Import smoke: vendored engine packages resolve from the workspace."""

from __future__ import annotations

from sift_parse.document_converter import DocumentConverter
from sift_parse.pipeline.standard_pdf_pipeline import StandardPdfPipeline


def test_document_converter_importable() -> None:
    assert DocumentConverter is not None


def test_document_converter_constructs() -> None:
    """Native pdf_parsers must load — import alone is not enough."""
    converter = DocumentConverter()
    assert converter is not None


def test_standard_pdf_pipeline_importable() -> None:
    assert StandardPdfPipeline is not None
