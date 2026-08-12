"""Qdrant dense vector store (optional backend; Phase 3 §4)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from urllib.parse import urlparse

import httpx

from sift_retrieve.hybrid import RetrieveHit

_MAX_BODY = 16 * 1024 * 1024


def collection_name(tenant_id: str, collection_id: str) -> str:
    """Qdrant collection name scoped by tenant + collection."""
    return f"{tenant_id}__{collection_id}"


class QdrantDenseStore:
    """Cosine dense search via Qdrant REST ``/points/search``."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            msg = "SIFT_QDRANT_URL must be an http(s) URL with a host"
            raise ValueError(msg)
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport

    def ensure_collection(self, *, tenant_id: str, collection_id: str, dim: int = 1024) -> None:
        name = collection_name(tenant_id, collection_id)
        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            exists = client.get(f"{self._base_url}/collections/{name}")
            if exists.status_code == httpx.codes.OK:
                return
            response = client.put(
                f"{self._base_url}/collections/{name}",
                json={
                    "vectors": {"size": dim, "distance": "Cosine"},
                },
            )
            response.raise_for_status()

    def upsert_points(
        self,
        *,
        tenant_id: str,
        collection_id: str,
        points: list[dict[str, Any]],
    ) -> None:
        name = collection_name(tenant_id, collection_id)
        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            response = client.put(
                f"{self._base_url}/collections/{name}/points",
                json={"points": points},
            )
            response.raise_for_status()

    def search(
        self,
        *,
        query_vector: Sequence[float],
        tenant_id: str,
        collection_id: str,
        limit: int = 50,
        document_ids: Sequence[str] | None = None,
    ) -> list[RetrieveHit]:
        if document_ids is not None and len(document_ids) == 0:
            return []
        name = collection_name(tenant_id, collection_id)
        must: list[dict[str, Any]] = [
            {"key": "tenant_id", "match": {"value": tenant_id}},
            {"key": "collection_id", "match": {"value": collection_id}},
        ]
        if document_ids is not None:
            must.append({"key": "document_id", "match": {"any": list(document_ids)}})
        body = {
            "vector": [float(x) for x in query_vector],
            "limit": limit,
            "with_payload": True,
            "filter": {"must": must},
        }
        with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
            response = client.post(
                f"{self._base_url}/collections/{name}/points/search",
                json=body,
            )
            response.raise_for_status()
            if len(response.content) > _MAX_BODY:
                msg = "Qdrant search response exceeds size limit"
                raise RuntimeError(msg)
            payload = response.json()
        rows = payload.get("result") or []
        hits: list[RetrieveHit] = []
        for row in rows:
            pl = row.get("payload") or {}
            hits.append(
                RetrieveHit(
                    chunk_id=str(pl.get("chunk_id") or row.get("id")),
                    document_id=str(pl.get("document_id") or ""),
                    score=float(row.get("score") or 0.0),
                )
            )
        return hits
