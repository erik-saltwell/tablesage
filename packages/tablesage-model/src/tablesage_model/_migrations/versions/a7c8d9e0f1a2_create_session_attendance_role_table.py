"""create session_attendance_role table

Revision ID: a7c8d9e0f1a2
Revises: f6b7c8d9e0f1
Create Date: 2026-08-18 00:00:06.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c8d9e0f1a2"
down_revision: str | Sequence[str] | None = "f6b7c8d9e0f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "session_attendance_role",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attendance_id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["attendance_id"], ["session_attendance.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attendance_id", "name", name="uq_session_attendance_role_attendance_id_name"),
        sa.CheckConstraint("trim(name) != ''", name="ck_session_attendance_role_name_non_blank"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("session_attendance_role")
