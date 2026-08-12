"""p3-2: chunk_embeddings migration contract (fails until 0007 lands)."""

from __future__ import annotations

from pathlib import Path

VERSIONS = Path(__file__).resolve().parents[2] / "tools" / "db" / "migrations" / "versions"
MIGRATION = VERSIONS / "0007_chunk_embeddings.py"


def test_chunk_embeddings_migration_file_exists() -> None:
    assert MIGRATION.is_file(), "expected tools/db/migrations/versions/0007_chunk_embeddings.py"


def test_chunk_embeddings_migration_declares_pgvector_and_rls() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE TABLE chunk_embeddings" in text
    assert "vector(1024)" in text
    assert "sparse" in text
    assert "hnsw" in text.lower()
    assert "ENABLE ROW LEVEL SECURITY" in text
    assert "FORCE ROW LEVEL SECURITY" in text
    assert "chunk_embeddings_tenant_isolation" in text
    assert "down_revision" in text
    assert '"0006"' in text or "'0006'" in text
