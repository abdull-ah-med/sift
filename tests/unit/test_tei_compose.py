"""Phase 3 §2.1 — TEI compose + settings must be wired before embed worker."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy" / "compose" / "dev.yml"
MIN_HEALTHCHECK_RETRIES = 5


@pytest.fixture(scope="module")
def compose_doc() -> dict:
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def test_compose_tei_services_use_ml_profile_and_bge_models(compose_doc: dict) -> None:
    services = compose_doc["services"]
    tei = services["tei"]
    rerank = services["tei-rerank"]
    assert tei["profiles"] == ["ml"]
    assert rerank["profiles"] == ["ml"]
    assert "BAAI/bge-m3" in " ".join(tei["command"])
    assert "BAAI/bge-reranker-v2-m3" in " ".join(rerank["command"])
    assert tei["image"].startswith("ghcr.io/huggingface/text-embeddings-inference:cpu-")
    assert rerank["image"].startswith("ghcr.io/huggingface/text-embeddings-inference:cpu-")


def test_compose_tei_services_have_healthchecks(compose_doc: dict) -> None:
    services = compose_doc["services"]
    for name in ("tei", "tei-rerank"):
        hc = services[name].get("healthcheck")
        assert hc is not None, f"{name} missing healthcheck"
        assert "test" in hc
        assert hc.get("retries", 0) >= MIN_HEALTHCHECK_RETRIES


def test_compose_sift_env_points_at_tei_service_dns(compose_doc: dict) -> None:
    # x-sift-env is a Compose extension field at document root.
    env = compose_doc.get("x-sift-env") or compose_doc["services"]["sift-api"]["environment"]
    # After YAML merge, sift-api environment is expanded; check either form.
    if isinstance(env, dict) and "SIFT_EMBED_URL" in env:
        assert env["SIFT_EMBED_URL"] == "http://tei:80"
        assert env["SIFT_RERANK_URL"] == "http://tei-rerank:80"
    else:
        api_env = compose_doc["services"]["sift-api"]["environment"]
        assert api_env["SIFT_EMBED_URL"] == "http://tei:80"
        assert api_env["SIFT_RERANK_URL"] == "http://tei-rerank:80"
