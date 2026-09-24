"""Reduce session processing state to the Review Transcript draft pointer.

Process Session's step list replaced the three-phase Audio/Transcript/Outputs flow, so the stored
phase and failure columns are no longer read. Review Transcript drafts now start from the
spellchecked transcript (or a still-current completed review); drafts based on the old machine
transcript can no longer be resumed, so their pointers are cleared.

Revision ID: a9b0c1d2e3f4
Revises: f7a8b9c0d1e2
Create Date: 2026-09-24 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a9b0c1d2e3f4"
down_revision: str | Sequence[str] | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PHASES = "'audio', 'bootstrap_review', 'new_speaker_review', 'spelling', 'transcript', 'outputs'"


def upgrade() -> None:
    op.execute(
        "UPDATE session_processing_state SET draft_source_artifact = NULL, draft_source_modified_ns = NULL "
        "WHERE draft_source_artifact IS NOT NULL AND draft_source_artifact <> 'reviewed_transcript'"
    )
    with op.batch_alter_table("session_processing_state", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_session_processing_state_phase_valid", type_="check")
        batch_op.drop_constraint("ck_session_processing_state_failed_phase_valid", type_="check")
        batch_op.drop_constraint("ck_session_processing_state_draft_source_valid", type_="check")
        batch_op.drop_column("phase")
        batch_op.drop_column("failed_phase")
        batch_op.drop_column("failure_message")
        batch_op.create_check_constraint(
            "ck_session_processing_state_draft_source_valid",
            "draft_source_artifact is null or draft_source_artifact in ('spellchecked_transcript', 'reviewed_transcript')",
        )


def downgrade() -> None:
    op.execute(
        "UPDATE session_processing_state SET draft_source_artifact = NULL, draft_source_modified_ns = NULL "
        "WHERE draft_source_artifact = 'spellchecked_transcript'"
    )
    with op.batch_alter_table("session_processing_state", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_session_processing_state_draft_source_valid", type_="check")
        batch_op.add_column(sa.Column("phase", sa.String(), nullable=False, server_default="audio"))
        batch_op.add_column(sa.Column("failed_phase", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("failure_message", sa.String(), nullable=True))
        batch_op.create_check_constraint(
            "ck_session_processing_state_draft_source_valid",
            "draft_source_artifact is null or draft_source_artifact in ('transcript', 'reviewed_transcript')",
        )
        batch_op.create_check_constraint("ck_session_processing_state_phase_valid", f"phase in ({_PHASES})")
        batch_op.create_check_constraint(
            "ck_session_processing_state_failed_phase_valid", f"failed_phase is null or failed_phase in ({_PHASES})"
        )
