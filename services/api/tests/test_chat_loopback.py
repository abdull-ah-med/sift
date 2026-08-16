"""Unit tests for loopback OpenAI-compat chat generator (p4demo-2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import instructor
import pytest

from sift_api.routes.chat import (
    _EnvAnswerGenerator,
    _loopback_openai_url,
)
from sift_api.settings import get_settings
from sift_chat.schemas import LLMAnswer


def test_loopback_url_accepts_loopback_http() -> None:
    assert _loopback_openai_url("http://127.0.0.1:11434/v1") == "http://127.0.0.1:11434/v1"
    assert _loopback_openai_url("http://localhost:11434") == "http://localhost:11434/v1"
    assert _loopback_openai_url("http://[::1]:11434/v1") == "http://[::1]:11434/v1"


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "http://127.0.0.1.evil",
        "https://127.0.0.1",
        "http://127.0.0.1.attacker.com",
    ],
)
def test_loopback_url_rejects_non_loopback(url: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        _loopback_openai_url(url)


def test_no_llm_returns_insufficient_err_chat_no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("SIFT_LLM_API_KEY", "")
    monkeypatch.setenv("SIFT_CHAT_BASE_URL", "")
    monkeypatch.setenv("SIFT_LLM_PROVIDER", "")
    get_settings.cache_clear()
    answer = _EnvAnswerGenerator().generate(
        system="s",
        user="q",
        allowed_chunk_ids=["chunk_1"],
    )
    assert answer.insufficient is True
    assert "err_chat_no_llm" in answer.text
    assert "11434" in answer.text


def test_non_loopback_base_url_does_not_construct_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("SIFT_CHAT_BASE_URL", "http://example.com/v1")
    monkeypatch.setenv("SIFT_LLM_PROVIDER", "")
    get_settings.cache_clear()

    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("OpenAI client must not be constructed")

    monkeypatch.setattr("openai.OpenAI", boom)
    answer = _EnvAnswerGenerator().generate(system="s", user="q", allowed_chunk_ids=[])
    assert answer.insufficient is True
    assert "err_chat_llm_url" in answer.text


def test_loopback_uses_instructor_json_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("SIFT_CHAT_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("SIFT_LLM_PROVIDER", "")
    get_settings.cache_clear()
    captured: dict[str, Any] = {}

    class _FakeOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured["openai"] = kwargs

    def _from_openai(client: Any, mode: Any = None, **kwargs: Any) -> Any:
        captured["mode"] = mode
        captured["from_openai_kwargs"] = kwargs
        patched = MagicMock()
        patched.chat.completions.create.return_value = LLMAnswer(
            text="ok",
            cited_chunk_ids=[],
            confidence=1.0,
            insufficient=False,
        )
        return patched

    monkeypatch.setattr("openai.OpenAI", _FakeOpenAI)
    monkeypatch.setattr(instructor, "from_openai", _from_openai)
    answer = _EnvAnswerGenerator().generate(system="s", user="q", allowed_chunk_ids=[])
    assert answer.insufficient is False
    assert captured["mode"] is instructor.Mode.JSON
    assert captured["from_openai_kwargs"].get("max_retries") == 2
    assert str(captured["openai"]["base_url"]).startswith("http://127.0.0.1:11434/v1")
    assert float(captured["openai"]["timeout"]) >= 60.0
