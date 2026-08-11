"""Tests for GET /health/ready readiness contract."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from sift_api.main import app
from sift_api.readiness import CheckResult


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_ready_when_all_dependencies_ok_returns_200(client: TestClient) -> None:
    ok = CheckResult(ok=True, detail="ok")
    with (
        patch("sift_api.routes.health.check_postgres", new=AsyncMock(return_value=ok)),
        patch("sift_api.routes.health.check_valkey", new=AsyncMock(return_value=ok)),
        patch("sift_api.routes.health.check_storage", new=AsyncMock(return_value=ok)),
    ):
        response = client.get("/health/ready")

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["postgres"]["ok"] is True
    assert body["checks"]["valkey"]["ok"] is True
    assert body["checks"]["storage"]["ok"] is True


def test_ready_when_postgres_down_returns_503(client: TestClient) -> None:
    ok = CheckResult(ok=True, detail="ok")
    bad = CheckResult(ok=False, detail="connection refused")
    with (
        patch("sift_api.routes.health.check_postgres", new=AsyncMock(return_value=bad)),
        patch("sift_api.routes.health.check_valkey", new=AsyncMock(return_value=ok)),
        patch("sift_api.routes.health.check_storage", new=AsyncMock(return_value=ok)),
    ):
        response = client.get("/health/ready")

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["postgres"]["ok"] is False
