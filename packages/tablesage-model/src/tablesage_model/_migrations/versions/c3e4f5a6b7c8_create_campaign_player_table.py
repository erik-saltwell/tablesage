"""create campaign_player table

Revision ID: c3e4f5a6b7c8
Revises: b2d3e4f5a6b7
Create Date: 2026-08-18 00:00:02.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3e4f5a6b7c8"
down_revision: str | Sequence[str] | None = "b2d3e4f5a6b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "campaign_player",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("default_role_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaign.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "player_id", name="uq_campaign_player_campaign_id_player_id"),
        sa.CheckConstraint("trim(default_role_name) != ''", name="ck_campaign_player_default_role_name_non_blank"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("campaign_player")
