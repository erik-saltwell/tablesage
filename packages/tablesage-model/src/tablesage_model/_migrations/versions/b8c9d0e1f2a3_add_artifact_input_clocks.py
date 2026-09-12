"""Add logical modification clocks used by artifact freshness checks."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: str | Sequence[str] | None = "a7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("campaign", sa.Column("glossary_updated_at", sa.DateTime(), nullable=True))
    op.add_column("campaign", sa.Column("roster_updated_at", sa.DateTime(), nullable=True))
    op.execute(sa.text("UPDATE campaign SET glossary_updated_at = updated_at, roster_updated_at = updated_at"))
    with op.batch_alter_table("campaign") as batch_op:
        batch_op.alter_column("glossary_updated_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.alter_column("roster_updated_at", existing_type=sa.DateTime(), nullable=False)

    op.add_column("session", sa.Column("metadata_updated_at", sa.DateTime(), nullable=True))
    op.add_column("session", sa.Column("attendance_updated_at", sa.DateTime(), nullable=True))
    op.execute(sa.text("UPDATE session SET metadata_updated_at = updated_at, attendance_updated_at = updated_at"))
    with op.batch_alter_table("session") as batch_op:
        batch_op.alter_column("metadata_updated_at", existing_type=sa.DateTime(), nullable=False)
        batch_op.alter_column("attendance_updated_at", existing_type=sa.DateTime(), nullable=False)


def downgrade() -> None:
    op.drop_column("session", "attendance_updated_at")
    op.drop_column("session", "metadata_updated_at")
    op.drop_column("campaign", "roster_updated_at")
    op.drop_column("campaign", "glossary_updated_at")
