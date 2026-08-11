"""Add api_keys.hash_version for pepper rotation (ADR-0013).

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-11
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE api_keys
          ADD COLUMN hash_version smallint NOT NULL DEFAULT 1
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE api_keys DROP COLUMN IF EXISTS hash_version")
