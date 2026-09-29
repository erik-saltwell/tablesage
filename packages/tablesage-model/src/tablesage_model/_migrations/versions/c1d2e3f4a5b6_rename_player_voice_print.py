"""Rename the player's stored voice print field, preserving existing embeddings.

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-09-29 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: str | Sequence[str] | None = "b0c1d2e3f4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename the legacy column without changing stored values."""
    op.alter_column("player", "centroid_embedding", new_column_name="voice_print_embedding")


def downgrade() -> None:
    """Restore the historical column name without changing stored values."""
    op.alter_column("player", "voice_print_embedding", new_column_name="centroid_embedding")
