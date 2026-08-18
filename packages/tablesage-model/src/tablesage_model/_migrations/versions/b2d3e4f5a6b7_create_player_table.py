"""create player table

Revision ID: b2d3e4f5a6b7
Revises: a1c2d3e4f5a6
Create Date: 2026-08-18 00:00:01.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2d3e4f5a6b7"
down_revision: str | Sequence[str] | None = "a1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "player",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("centroid_embedding", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("embedding_dimension", sa.Integer(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_player_name"),
        sa.CheckConstraint("trim(name) != ''", name="ck_player_name_non_blank"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("player")
