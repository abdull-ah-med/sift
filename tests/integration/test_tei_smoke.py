"""Live TEI smoke: fixed string → 1024-d dense vector (Phase 3 §2.1).

Requires Compose profile ``ml`` healthy, or any reachable TEI at ``SIFT_TEI_URL``.
Skipped when the embed server is not up (laptop/CI without the ``ml`` profile).
"""

from __future__ import annotations

import os

import httpx
import pytest

FIXED_INPUT = "sift phase-3 tei smoke"
EXPECTED_DIM = 1024
HTTP_OK = 200


def _tei_base() -> str:
    return os.environ.get("SIFT_TEI_URL", "http://127.0.0.1:8080").rstrip("/")


def _tei_reachable(base: str) -> bool:
    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get(f"{base}/health")
            return r.status_code == HTTP_OK
    except (httpx.HTTPError, OSError):
        return False


@pytest.mark.integration
def test_tei_embed_fixed_string_returns_1024d() -> None:
    base = _tei_base()
    if not _tei_reachable(base):
        pytest.skip(f"TEI not reachable at {base}; start with --profile ml")

    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{base}/embed", json={"inputs": FIXED_INPUT})
        response.raise_for_status()
        payload = response.json()

    # TEI returns a list of vectors (one per input).
    assert isinstance(payload, list)
    assert len(payload) >= 1
    vector = payload[0]
    assert isinstance(vector, list)
    assert len(vector) == EXPECTED_DIM
    assert all(isinstance(x, (int, float)) for x in vector)
