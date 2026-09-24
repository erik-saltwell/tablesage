"""Drop the retired new-speaker bootstrap workflow's tables.

Process Session's Seed Player Voice Samples step replaced the bootstrap workflow; nothing reads its
run records or profile-contribution receipts any more. Voice clips it already added stay in player
folders.

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-09-24 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b0c1d2e3f4a5"
down_revision: str | Sequence[str] | None = "a9b0c1d2e3f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_bootstrap_profile_contribution_session_id", table_name="bootstrap_profile_contribution")
    op.drop_index("ix_bootstrap_profile_contribution_player_id", table_name="bootstrap_profile_contribution")
    op.drop_table("bootstrap_profile_contribution")
    op.drop_index("ix_session_bootstrap_run_session_id", table_name="session_bootstrap_run")
    op.drop_table("session_bootstrap_run")


def downgrade() -> None:
    op.create_table(
        "session_bootstrap_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("source_sha256", sa.String(), nullable=False),
        sa.Column("attendee_fingerprint", sa.String(), nullable=False),
        sa.Column("settings_fingerprint", sa.String(), nullable=False),
        sa.Column("prompt_fingerprint", sa.String(), nullable=False),
        sa.Column("embedding_model_id", sa.String(), nullable=False),
        sa.Column("targets_json", sa.String(), nullable=False),
        sa.Column("attendees_json", sa.String(), nullable=False),
        sa.Column("references_json", sa.String(), nullable=False),
        sa.Column("manifest_sha256", sa.String(), nullable=True),
        sa.Column("manifest_revision", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(), nullable=True),
        sa.Column("failure_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("schema_version >= 1", name="ck_session_bootstrap_run_schema_version"),
        sa.CheckConstraint("manifest_revision >= 0", name="ck_session_bootstrap_run_manifest_revision"),
        sa.CheckConstraint(
            "operation is null or operation in ('preparing', 'identifying', 'finalizing')",
            name="ck_session_bootstrap_run_operation_valid",
        ),
        sa.ForeignKeyConstraint(["session_id"], ["session.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_bootstrap_run_session_id", "session_bootstrap_run", ["session_id"])
    op.create_table(
        "bootstrap_profile_contribution",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("player_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_transcript_sha256", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("staged_manifest_sha256", sa.String(), nullable=True),
        sa.Column("clip_count", sa.Integer(), nullable=False),
        sa.Column("failure_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "state in ('pending', 'prepared', 'committed', 'no_usable_clips', 'skipped_existing_profile', 'failed')",
            name="ck_bootstrap_profile_contribution_state_valid",
        ),
        sa.CheckConstraint("clip_count >= 0", name="ck_bootstrap_profile_contribution_clip_count"),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["session_bootstrap_run.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["session.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "player_id", name="uq_bootstrap_profile_contribution_session_player"),
    )
    op.create_index("ix_bootstrap_profile_contribution_player_id", "bootstrap_profile_contribution", ["player_id"])
    op.create_index("ix_bootstrap_profile_contribution_session_id", "bootstrap_profile_contribution", ["session_id"])
