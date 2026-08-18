"""create session table

Revision ID: e5a6b7c8d9e0
Revises: d4f5a6b7c8d9
Create Date: 2026-08-18 00:00:04.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5a6b7c8d9e0"
down_revision: str | Sequence[str] | None = "d4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaign.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "sequence_number", name="uq_session_campaign_id_sequence_number"),
        sa.CheckConstraint("trim(name) != ''", name="ck_session_name_non_blank"),
        sa.CheckConstraint(
            "status in ('draft', 'ready', 'processing', 'processed', 'needs_review', 'failed')",
            name="ck_session_status_valid",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("session")
