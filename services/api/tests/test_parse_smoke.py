from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from sift_api.main import app
from sift.parse.smoke import ParseSmokeResult

CORPUS = Path(__file__).resolve().parents[3] / "evals" / "corpus"
_MIN_DIGITAL_PDFS = 5


def test_parse_smoke_returns_counts_when_pipeline_ok() -> None:
    client = TestClient(app)
    fake = ParseSmokeResult(
        blocks=4,
        markdown_length=12,
        source="/tmp/x.pdf",
        engine="injected",
    )

    with patch(
        "sift_api.routes.parse_smoke.run_parse_smoke",
        return_value=fake,
    ):
        response = client.post(
            "/internal/parse-smoke",
            files={"file": ("sample.pdf", b"%PDF-1.1\n", "application/pdf")},
        )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "blocks": 4,
        "markdown_length": 12,
        "source_filename": "sample.pdf",
        "engine": "injected",
    }


def test_parse_smoke_returns_503_when_stack_missing() -> None:
    client = TestClient(app)

    with patch(
        "sift_api.routes.parse_smoke.run_parse_smoke",
        side_effect=ImportError("docling"),
    ):
        response = client.post(
            "/internal/parse-smoke",
            files={"file": ("sample.pdf", b"%PDF-1.1\n", "application/pdf")},
        )

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_parse_smoke_rejects_empty_upload() -> None:
    client = TestClient(app)
    response = client.post(
        "/internal/parse-smoke",
        files={"file": ("sample.pdf", b"", "application/pdf")},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_parse_smoke_digital_corpus_via_http() -> None:
    client = TestClient(app)
    pdfs = sorted(CORPUS.glob("digital-*.pdf"))
    assert len(pdfs) >= _MIN_DIGITAL_PDFS
    for pdf in pdfs:
        response = client.post(
            "/internal/parse-smoke",
            files={"file": (pdf.name, pdf.read_bytes(), "application/pdf")},
        )
        assert response.status_code == HTTPStatus.OK, pdf.name
        body = response.json()
        assert body["blocks"] > 0, pdf.name
        assert body["markdown_length"] > 0, pdf.name
        assert body["engine"] == "pypdfium2"
