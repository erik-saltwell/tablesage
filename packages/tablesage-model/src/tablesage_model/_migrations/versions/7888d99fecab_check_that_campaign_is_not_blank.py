"""check that campaign is not blank

Revision ID: 7888d99fecab
Revises: f2ca86ee33d1
Create Date: 2026-08-15 18:28:56.697264

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7888d99fecab"
down_revision: str | Sequence[str] | None = "f2ca86ee33d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("campaign") as batch_op:
        batch_op.create_check_constraint("ck_campaign_name_non_blank", "trim(name) != ''")


def downgrade() -> None:
    with op.batch_alter_table("campaign") as batch_op:
        batch_op.drop_constraint("ck_campaign_name_non_blank", type_="check")
