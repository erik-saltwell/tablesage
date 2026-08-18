"""decouple player from campaign

Revision ID: a1c2d3e4f5a6
Revises: 7888d99fecab
Create Date: 2026-08-18 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "7888d99fecab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("campaign") as batch_op:
        batch_op.drop_column("default_gm_name")
        batch_op.create_unique_constraint("uq_campaign_name", ["name"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("campaign") as batch_op:
        batch_op.drop_constraint("uq_campaign_name", type_="unique")
        batch_op.add_column(sa.Column("default_gm_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
