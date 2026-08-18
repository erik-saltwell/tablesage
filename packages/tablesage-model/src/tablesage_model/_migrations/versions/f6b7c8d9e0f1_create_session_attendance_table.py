"""create session_attendance table

Revision ID: f6b7c8d9e0f1
Revises: e5a6b7c8d9e0
Create Date: 2026-08-18 00:00:05.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6b7c8d9e0f1"
down_revision: str | Sequence[str] | None = "e5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "session_attendance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["session.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "player_id", name="uq_session_attendance_session_id_player_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("session_attendance")
