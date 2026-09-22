from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


class BootstrapProfileContribution(SQLModel, table=True):
    """Receipt for one bootstrap target's eventual profile contribution.

    Receipts deliberately outlive workflow-state cleanup so a later review cannot silently
    add another automatic contribution for the same session/player pair.
    """

    __tablename__ = "bootstrap_profile_contribution"
    __table_args__ = (
        UniqueConstraint("session_id", "player_id", name="uq_bootstrap_profile_contribution_session_player"),
        CheckConstraint(
            "state in ('pending', 'prepared', 'committed', 'no_usable_clips', 'skipped_existing_profile', 'failed')",
            name="ck_bootstrap_profile_contribution_state_valid",
        ),
        CheckConstraint("clip_count >= 0", name="ck_bootstrap_profile_contribution_clip_count"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="session.id", ondelete="CASCADE", index=True)
    player_id: uuid.UUID = Field(foreign_key="player.id", index=True)
    run_id: uuid.UUID = Field(foreign_key="session_bootstrap_run.id", ondelete="CASCADE")
    reviewed_transcript_sha256: str | None = Field(default=None)
    state: str = Field(default="pending")
    staged_manifest_sha256: str | None = Field(default=None)
    clip_count: int = Field(default=0)
    failure_message: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
