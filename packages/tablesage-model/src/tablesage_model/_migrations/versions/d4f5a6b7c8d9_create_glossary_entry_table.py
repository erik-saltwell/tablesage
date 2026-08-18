"""create glossary_entry table

Revision ID: d4f5a6b7c8d9
Revises: c3e4f5a6b7c8
Create Date: 2026-08-18 00:00:03.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4f5a6b7c8d9"
down_revision: str | Sequence[str] | None = "c3e4f5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "glossary_entry",
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("term", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaign.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("campaign_id", "id"),
        sa.UniqueConstraint("campaign_id", "term", name="uq_glossary_entry_campaign_id_term"),
        sa.CheckConstraint("trim(term) != ''", name="ck_glossary_entry_term_non_blank"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("glossary_entry")
