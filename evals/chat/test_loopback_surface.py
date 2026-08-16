"""Golden: loopback chat + auto-index helpers exist (fails on origin/dev)."""

from __future__ import annotations

from pathlib import Path

import yaml

from sift_api.ingest_finalize import persist_chunks_and_enqueue_embed
from sift_api.routes import chat as chat_mod

FIXTURE = Path(__file__).resolve().parent / "loopback-surface.yaml"


def test_loopback_and_auto_index_surface() -> None:
    doc = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    assert doc["require_mode"] == "instructor.Mode.JSON"
    assert hasattr(chat_mod, "_loopback_openai_url")
    source = Path(chat_mod.__file__).read_text(encoding="utf-8")
    assert "instructor.Mode.JSON" in source
    assert "127.0.0.1" in source
    assert callable(persist_chunks_and_enqueue_embed)
    assert "err_chat_no_llm" in source
