"""Chat API OpenAPI + schema contracts (no live Postgres)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from sift_api.main import app
from sift_api.schemas import ChatAskRequest, ChatSessionCreate


def test_chat_openapi_paths_registered() -> None:
    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    paths = schema.get("paths") or {}
    expected = [
        "/v1/collections/{collection_id}/chat/sessions",
        "/v1/collections/{collection_id}/chat",
        "/v1/chat/sessions/{session_id}",
        "/v1/chat/resume",
        "/v1/chat/turns/{turn_id}/citations",
    ]
    for path in expected:
        assert path in paths, f"missing OpenAPI path {path}"


def test_chat_ask_request_rejects_empty_message() -> None:
    with pytest.raises(ValidationError):
        ChatAskRequest(message="")


def test_chat_session_create_accepts_null_title() -> None:
    body = ChatSessionCreate(title=None)
    assert body.title is None
