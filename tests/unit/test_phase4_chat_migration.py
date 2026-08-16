"""p4: chat_sessions / chat_turns migration contract."""

from __future__ import annotations

from pathlib import Path

VERSIONS = Path(__file__).resolve().parents[2] / "tools" / "db" / "migrations" / "versions"
MIGRATION = VERSIONS / "0009_phase4_chat.py"


def test_phase4_chat_migration_file_exists() -> None:
    assert MIGRATION.is_file()


def test_phase4_chat_migration_declares_tables_and_rls() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE TABLE chat_sessions" in text
    assert "CREATE TABLE chat_turns" in text
    assert "ENABLE ROW LEVEL SECURITY" in text
    assert "FORCE ROW LEVEL SECURITY" in text
    assert "chat_sessions" in text
    assert "rolling_summary" in text
    assert "long_term_facts" in text
    assert "down_revision" in text
