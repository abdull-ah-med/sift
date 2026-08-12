"""TEI rerank client (BGE reranker)."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

_MAX_BODY = 16 * 1024 * 1024


class TeiReranker:
    """Call TEI ``/rerank``; never logs query or passage text."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            msg = "SIFT_TEI_RERANK_URL must be an http(s) URL with a host"
            raise ValueError(msg)
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport

    def rerank(
        self,
        *,
        query: str,
        documents: list[tuple[str, str]],
    ) -> list[tuple[str, float]]:
        """Rerank ``(id, text)`` pairs; return ``(id, score)`` ordered best-first."""
        if not documents:
            return []
        texts = [text for _cid, text in documents]
        ids = [cid for cid, _text in documents]
        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            response = client.post(
                f"{self._base_url}/rerank",
                json={"query": query, "texts": texts},
            )
            response.raise_for_status()
            if len(response.content) > _MAX_BODY:
                msg = "TEI /rerank response exceeds size limit"
                raise RuntimeError(msg)
            payload: Any = response.json()

        # TEI may return [{index, score}, ...] or a list of scores.
        scored: list[tuple[str, float]] = []
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            for row in payload:
                idx = int(row["index"])
                scored.append((ids[idx], float(row["score"])))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored
        if isinstance(payload, list):
            pairs = [(ids[i], float(s)) for i, s in enumerate(payload)]
            pairs.sort(key=lambda x: x[1], reverse=True)
            return pairs
        msg = "unexpected TEI /rerank payload shape"
        raise RuntimeError(msg)
