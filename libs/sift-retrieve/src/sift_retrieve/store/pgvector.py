"""pgvector dense search."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Connection, text

from sift_retrieve.hybrid import RetrieveHit

_ELIGIBLE_REVIEW = "('approved', 'edited')"


class PgvectorDenseStore:
    """Cosine distance search over ``chunk_embeddings``."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def search(
        self,
        *,
        query_vector: Sequence[float],
        tenant_id: str,
        collection_id: str,
        limit: int = 50,
        document_ids: Sequence[str] | None = None,
    ) -> list[RetrieveHit]:
        # Empty allowlist = deny-all (ACL semantics), distinct from None = unrestricted.
        if document_ids is not None and len(document_ids) == 0:
            return []

        vec_literal = "[" + ",".join(str(float(x)) for x in query_vector) + "]"
        doc_filter = ""
        params: dict[str, object] = {
            "tenant_id": tenant_id,
            "collection_id": collection_id,
            "limit": limit,
            "embedding": vec_literal,
        }
        if document_ids is not None:
            doc_filter = "AND c.document_id = ANY(:document_ids)"
            params["document_ids"] = list(document_ids)
        rows = self._conn.execute(
            text(
                f"""
                SELECT e.chunk_id, c.document_id,
                       1 - (e.embedding <=> CAST(:embedding AS vector)) AS score
                FROM chunk_embeddings e
                JOIN chunks c ON c.id = e.chunk_id
                JOIN documents d ON d.id = c.document_id AND d.deleted_at IS NULL
                WHERE e.tenant_id = :tenant_id
                  AND e.collection_id = :collection_id
                  AND c.review_state IN {_ELIGIBLE_REVIEW}
                  {doc_filter}
                ORDER BY e.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            ),
            params,
        ).mappings()
        return [
            RetrieveHit(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                score=float(r["score"]),
            )
            for r in rows
        ]
