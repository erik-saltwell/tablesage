"""Remove the campaign roster.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-09-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: str | Sequence[str] | None = "c9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("campaign_player")
    with op.batch_alter_table("campaign") as batch_op:
        batch_op.drop_column("roster_updated_at")


def downgrade() -> None:
    with op.batch_alter_table("campaign") as batch_op:
        batch_op.add_column(sa.Column("roster_updated_at", sa.DateTime(), nullable=True))
    op.execute(sa.text("UPDATE campaign SET roster_updated_at = updated_at"))
    with op.batch_alter_table("campaign") as batch_op:
        batch_op.alter_column("roster_updated_at", existing_type=sa.DateTime(), nullable=False)

    op.create_table(
        "campaign_player",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaign.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "player_id", name="uq_campaign_player_campaign_id_player_id"),
    )
