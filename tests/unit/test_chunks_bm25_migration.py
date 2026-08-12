"""BM25 index migration contract (chunks BM25 deferred from Phase 2)."""

from __future__ import annotations

from pathlib import Path

VERSIONS = Path(__file__).resolve().parents[2] / "tools" / "db" / "migrations" / "versions"
MIGRATION = VERSIONS / "0008_chunks_bm25.py"


def test_chunks_bm25_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_chunks_bm25_migration_creates_bm25_index() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    assert "chunks_bm25_idx" in text
    assert "USING bm25" in text or "USING paradedb" in text
    assert "text_contextualized" in text
    assert "key_field" in text
    assert '"0007"' in text or "'0007'" in text
