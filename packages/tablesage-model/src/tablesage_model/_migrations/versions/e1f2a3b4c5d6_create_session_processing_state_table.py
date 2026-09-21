"""Create session processing state table.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-09-20 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: str | Sequence[str] | None = "d0e1f2a3b4c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "session_processing_state",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("draft_source_artifact", sa.String(), nullable=True),
        sa.Column("draft_source_modified_ns", sa.BigInteger(), nullable=True),
        sa.Column("failed_phase", sa.String(), nullable=True),
        sa.Column("failure_message", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("phase in ('audio', 'transcript', 'outputs')", name="ck_session_processing_state_phase_valid"),
        sa.CheckConstraint(
            "draft_source_artifact is null or draft_source_artifact in ('transcript', 'reviewed_transcript')",
            name="ck_session_processing_state_draft_source_valid",
        ),
        sa.CheckConstraint(
            "(draft_source_artifact is null and draft_source_modified_ns is null) "
            "or (draft_source_artifact is not null and draft_source_modified_ns is not null and draft_source_modified_ns >= 0)",
            name="ck_session_processing_state_draft_source_complete",
        ),
        sa.CheckConstraint(
            "failed_phase is null or failed_phase in ('audio', 'transcript', 'outputs')",
            name="ck_session_processing_state_failed_phase_valid",
        ),
        sa.ForeignKeyConstraint(["session_id"], ["session.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )


def downgrade() -> None:
    op.drop_table("session_processing_state")
