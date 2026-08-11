"""Import smoke: vendored engine packages resolve from the workspace."""

from __future__ import annotations


def test_document_converter_importable() -> None:
    from sift_parse.document_converter import DocumentConverter

    assert DocumentConverter is not None


def test_standard_pdf_pipeline_importable() -> None:
    from sift_parse.pipeline.standard_pdf_pipeline import StandardPdfPipeline

    assert StandardPdfPipeline is not None
