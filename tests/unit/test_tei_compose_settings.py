"""p3-1: TEI compose + settings contracts (Phase 3 §2.1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
import yaml  # type: ignore[import-untyped]

from sift_api.settings import Settings, get_settings

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy" / "compose" / "dev.yml"
ENV_EXAMPLE = ROOT / ".env.example"
MIN_HEALTHCHECK_START_PERIOD_S = 60


def _compose_doc() -> dict[str, Any]:
    loaded = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    return cast(dict[str, Any], loaded)


def test_tei_services_declare_healthchecks_and_models() -> None:
    doc = _compose_doc()
    services = doc["services"]

    tei = services["tei"]
    rerank = services["tei-rerank"]

    assert tei.get("profiles") == ["ml"]
    assert rerank.get("profiles") == ["ml"]
    assert "sha256:" in str(tei["image"])
    assert "sha256:" in str(rerank["image"])
    assert "latest" not in str(tei["image"]).lower()
    compose_text = COMPOSE.read_text(encoding="utf-8")
    assert "HF_HUB_CACHE" in compose_text
    assert "HUGGING_FACE_HUB_CACHE" not in compose_text

    tei_cmd = " ".join(tei["command"])
    rerank_cmd = " ".join(rerank["command"])
    assert "BAAI/bge-m3" in tei_cmd
    assert "BAAI/bge-reranker-v2-m3" in rerank_cmd
    assert "--max-batch-tokens" in tei_cmd
    assert "--max-batch-tokens" in rerank_cmd

    assert "healthcheck" in tei
    assert "healthcheck" in rerank
    assert "test" in tei["healthcheck"]
    assert "test" in rerank["healthcheck"]
    tei_hc = " ".join(str(x) for x in tei["healthcheck"]["test"])
    assert "curl" in tei_hc
    assert "/health" in tei_hc
    tei_start = int(str(tei["healthcheck"].get("start_period", "0s")).rstrip("s"))
    rerank_start = int(str(rerank["healthcheck"].get("start_period", "0s")).rstrip("s"))
    assert tei_start >= MIN_HEALTHCHECK_START_PERIOD_S
    assert rerank_start >= MIN_HEALTHCHECK_START_PERIOD_S


def test_compose_env_exposes_sift_tei_urls() -> None:
    text = COMPOSE.read_text(encoding="utf-8")
    assert "SIFT_TEI_URL:" in text
    assert "SIFT_TEI_RERANK_URL:" in text
    assert "http://tei:80" in text
    assert "http://tei-rerank:80" in text


def test_env_example_documents_tei_urls() -> None:
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "SIFT_TEI_URL=" in text
    assert "SIFT_TEI_RERANK_URL=" in text
    assert "SIFT_TEI_MODEL=" in text or "SIFT_EMBED_MODEL=" in text


def test_settings_reads_tei_urls_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("SIFT_TEI_URL", "http://tei-test:8080")
    monkeypatch.setenv("SIFT_TEI_RERANK_URL", "http://tei-rerank-test:8081")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.sift_tei_url == "http://tei-test:8080"
    assert settings.sift_tei_rerank_url == "http://tei-rerank-test:8081"
    get_settings.cache_clear()


def test_settings_default_tei_urls_point_at_localhost_ports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()
    monkeypatch.delenv("SIFT_TEI_URL", raising=False)
    monkeypatch.delenv("SIFT_TEI_RERANK_URL", raising=False)
    monkeypatch.delenv("SIFT_TEI_MODEL", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.sift_tei_url == "http://127.0.0.1:8080"
    assert settings.sift_tei_rerank_url == "http://127.0.0.1:8081"
    assert settings.sift_tei_model == "BAAI/bge-m3"
    get_settings.cache_clear()
