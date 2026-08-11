from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from sift_api.main import app
from sift_api.routes.health import HealthResponse


def test_health_returns_ok_when_service_up() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


def test_health_rejects_unknown_fields_in_schema() -> None:
    """Contract: HealthResponse forbids extras (enforced at model boundary)."""
    with pytest.raises(ValidationError):
        HealthResponse.model_validate({"status": "ok", "extra": True})
