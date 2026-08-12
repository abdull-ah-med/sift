"""Search CLI helpers (Phase 3 §7)."""

from __future__ import annotations

from typing import Any


def resolve_collection_id(collections: list[dict[str, Any]], collection: str) -> str:
    """Resolve ``--collection`` slug or id against ``GET /v1/collections``."""
    for row in collections:
        if row.get("id") == collection or row.get("slug") == collection:
            return str(row["id"])
    msg = f"collection not found: {collection}"
    raise LookupError(msg)


def format_search_rows(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Flatten search hits for a Rich table (snippet truncated)."""
    rows: list[dict[str, str]] = []
    for hit in payload.get("results") or []:
        score = hit.get("rerank_score")
        if score is None:
            score = hit.get("score", 0.0)
        text = str(hit.get("text") or "")
        snippet = text if len(text) <= 120 else text[:117] + "..."
        path = hit.get("section_path") or []
        pages = hit.get("page_numbers") or []
        rows.append(
            {
                "document": str(hit.get("document_title") or hit.get("document_id") or ""),
                "score": f"{float(score):.3f}",
                "pages": ",".join(str(p) for p in pages),
                "section": " / ".join(str(p) for p in path),
                "snippet": snippet,
                "chunk_id": str(hit.get("chunk_id") or ""),
            }
        )
    return rows


def format_search_json(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
