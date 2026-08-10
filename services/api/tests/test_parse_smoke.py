from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from sift_api.main import app
from sift_parse.smoke import ParseSmokeResult


def test_parse_smoke_returns_counts_when_pipeline_ok() -> None:
    client = TestClient(app)
    fake = ParseSmokeResult(blocks=4, markdown_length=12, source="/tmp/x.pdf")

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
