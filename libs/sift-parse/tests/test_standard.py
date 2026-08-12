"""StandardPdfParser unit + gated integration tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from sift.parse import MissingModelWeightsError, ParseConfig, StandardPdfParser


def test_standard_pdf_parser_refuses_missing_weights(tmp_path: Path) -> None:
    empty = tmp_path / "models"
    empty.mkdir()
    parser = StandardPdfParser(artifacts_path=empty)
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.1\n%\xe2\xe3\xcf\xd3\n")
    with pytest.raises(MissingModelWeightsError) as excinfo:
        parser.parse(pdf, ParseConfig())
    assert "docling-project/docling-layout-heron" in str(excinfo.value)


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("SIFT_HAVE_PARSE_WEIGHTS") != "1",
    reason="requires prefetched parse weights (SIFT_HAVE_PARSE_WEIGHTS=1)",
)
def test_standard_pdf_parser_produces_typed_blocks(tmp_path: Path) -> None:
    """Parse a tiny digital PDF into more than one BlockType when possible."""
    # Minimal one-page PDF with Helvetica text (no external deps to author).
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
        b"4 0 obj<< /Length 68 >>stream\n"
        b"BT /F1 24 Tf 72 720 Td (Hello StandardPdf) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"0000000266 00000 n \n0000000384 00000 n \n"
        b"trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n457\n%%EOF\n"
    )
    pdf = tmp_path / "hello.pdf"
    pdf.write_bytes(pdf_bytes)

    result = StandardPdfParser().parse(pdf, ParseConfig())
    assert result.metadata.page_count >= 1
    assert len(result.blocks) >= 1
    types = {b.block_type for b in result.blocks}
    assert types  # at least one typed block
