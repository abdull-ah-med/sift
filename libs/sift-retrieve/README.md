# sift-retrieve

Hybrid dense (pgvector) + BM25 (ParadeDB) retrieval with RRF (k=60) and optional TEI rerank.

Dense-only embeddings per ADR-0021; lexical path is BM25 (no invented BGE-M3 sparse).
