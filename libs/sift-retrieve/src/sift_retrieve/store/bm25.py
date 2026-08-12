"""ParadeDB BM25 lexical search."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Connection, text

from sift_retrieve.hybrid import RetrieveHit

_ELIGIBLE_REVIEW = "('approved', 'edited')"


def phrase_query(query: str) -> str:
    """Wrap ``query`` as a Tantivy/ParadeDB phrase so operators are not parsed as DSL."""
    escaped = query.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


class ParadeBm25Store:
    """BM25 over ``chunks.text_contextualized`` via pg_search."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def search(
        self,
        *,
        query: str,
        tenant_id: str,
        collection_id: str,
        limit: int = 50,
        document_ids: Sequence[str] | None = None,
    ) -> list[RetrieveHit]:
        # Empty allowlist = deny-all (ACL semantics), distinct from None = unrestricted.
        if document_ids is not None and len(document_ids) == 0:
            return []

        doc_filter = ""
        params: dict[str, object] = {
            "query": phrase_query(query),
            "tenant_id": tenant_id,
            "collection_id": collection_id,
            "limit": limit,
        }
        if document_ids is not None:
            doc_filter = "AND c.document_id = ANY(:document_ids)"
            params["document_ids"] = list(document_ids)
        rows = self._conn.execute(
            text(
                f"""
                SELECT c.id AS chunk_id, c.document_id,
                       paradedb.score(c.id) AS score
                FROM chunks c
                JOIN documents d ON d.id = c.document_id AND d.deleted_at IS NULL
                WHERE c.tenant_id = :tenant_id
                  AND c.collection_id = :collection_id
                  AND c.review_state IN {_ELIGIBLE_REVIEW}
                  AND c.text_contextualized @@@ :query
                  {doc_filter}
                ORDER BY score DESC
                LIMIT :limit
                """
            ),
            params,
        ).mappings()
        return [
            RetrieveHit(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                score=float(r["score"] or 0.0),
            )
            for r in rows
        ]
