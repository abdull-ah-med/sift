"""Settings expose TEI embed/rerank URLs (Phase 3 §2.1)."""

from __future__ import annotations

from sift_api.settings import Settings


def test_settings_loads_tei_embed_and_rerank_urls() -> None:
    s = Settings.model_validate(
        {
            "SIFT_EMBED_URL": "http://127.0.0.1:8080",
            "SIFT_RERANK_URL": "http://127.0.0.1:8081",
            "SIFT_EMBED_MODEL": "BAAI/bge-m3",
        }
    )
    assert s.sift_embed_url == "http://127.0.0.1:8080"
    assert s.sift_rerank_url == "http://127.0.0.1:8081"
    assert s.sift_embed_model == "BAAI/bge-m3"
