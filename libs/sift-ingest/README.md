# sift-ingest

Extract → chunk pipeline (absorbs vendor `sift-ingest` / LongParser patterns).

Phase 2 ships `chunk_blocks()` — one chunk per non-rejected block with a
lightweight contextual prefix. Vendored HybridChunker + LLM contextual
prefixes replace this in a later Phase 2 slice.
