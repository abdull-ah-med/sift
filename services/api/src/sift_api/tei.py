"""TEI HTTP client for BGE-M3 embeddings (Phase 3 §2.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class TeiEmbedResult:
    dense: list[list[float]]


class TeiClient:
    """Thin client over Hugging Face Text Embeddings Inference `/embed`."""

    def __init__(
        self,
        *,
        base_url: str,
        transport: httpx.BaseTransport | None = None,
        expected_dim: int = 1024,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport
        self.expected_dim = expected_dim
        self.timeout = timeout

    def embed(self, texts: list[str]) -> TeiEmbedResult:
        if not texts:
            return TeiEmbedResult(dense=[])
        with httpx.Client(transport=self.transport, timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/embed",
                json={"inputs": texts},
            )
            response.raise_for_status()
            payload: Any = response.json()
        embeddings = _extract_embeddings(payload)
        for row in embeddings:
            if len(row) != self.expected_dim:
                raise ValueError(
                    f"TEI embedding dim {len(row)} != expected {self.expected_dim} (BGE-M3=1024)"
                )
        return TeiEmbedResult(dense=embeddings)


def _extract_embeddings(payload: Any) -> list[list[float]]:
    if isinstance(payload, list):
        if payload and isinstance(payload[0], (int, float)):
            return [list(map(float, payload))]
        return [list(map(float, row)) for row in payload]
    if isinstance(payload, dict):
        if "embeddings" in payload:
            return [list(map(float, row)) for row in payload["embeddings"]]
        if "data" in payload:
            rows = []
            for item in payload["data"]:
                rows.append(list(map(float, item["embedding"])))
            return rows
    raise ValueError(f"unrecognized TEI embed response shape: {type(payload)!r}")
