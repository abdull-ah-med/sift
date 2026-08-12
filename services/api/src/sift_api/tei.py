"""HTTP client for Text Embeddings Inference (dense-only; ADR-0021)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

_MAX_TEI_BODY_BYTES = 16 * 1024 * 1024  # 16 MiB


class TeiClient:
    """Call TEI ``/embed`` for dense vectors. Sparse is intentionally unused."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str = "BAAI/bge-m3",
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
        max_body_bytes: int = _MAX_TEI_BODY_BYTES,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            msg = "SIFT_TEI_URL must be an http(s) URL with a host"
            raise ValueError(msg)
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._transport = transport
        self._max_body_bytes = max_body_bytes

    def embed(self, texts: list[str], *, batch_size: int = 64) -> list[list[float]]:
        """Return one dense vector per input text (BGE-M3 → 1024-d)."""
        if not texts:
            return []
        out: list[list[float]] = []
        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response = client.post(
                    f"{self._base_url}/embed",
                    json={"inputs": batch if len(batch) > 1 else batch[0]},
                )
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length is not None and int(content_length) > self._max_body_bytes:
                    msg = "TEI /embed response exceeds size limit"
                    raise RuntimeError(msg)
                raw = response.content
                if len(raw) > self._max_body_bytes:
                    msg = "TEI /embed response exceeds size limit"
                    raise RuntimeError(msg)
                payload: Any = response.json()
                if not isinstance(payload, list) or not payload:
                    msg = "TEI /embed returned empty or non-list payload"
                    raise RuntimeError(msg)
                # Single-string input may return a flat vector.
                if payload and isinstance(payload[0], (int, float)):
                    out.append([float(x) for x in payload])
                else:
                    for row in payload:
                        out.append([float(x) for x in row])
        return out
