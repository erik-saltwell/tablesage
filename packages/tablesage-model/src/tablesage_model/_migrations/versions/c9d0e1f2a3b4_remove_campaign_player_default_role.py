"""Remove campaign-level player roles."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: str | Sequence[str] | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("campaign_player") as batch_op:
        batch_op.drop_constraint("ck_campaign_player_default_role_name_non_blank", type_="check")
        batch_op.drop_column("default_role_name")


def downgrade() -> None:
    with op.batch_alter_table("campaign_player") as batch_op:
        batch_op.add_column(sa.Column("default_role_name", sa.String(), nullable=False, server_default="game-master"))
        batch_op.create_check_constraint("ck_campaign_player_default_role_name_non_blank", "trim(default_role_name) != ''")

    with op.batch_alter_table("campaign_player") as batch_op:
        batch_op.alter_column("default_role_name", existing_type=sa.String(), server_default=None)
