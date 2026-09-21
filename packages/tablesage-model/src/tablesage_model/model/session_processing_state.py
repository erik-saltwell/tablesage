from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class SessionProcessingPhase(StrEnum):
    """The resumable primary-flow stage a Session should reopen."""

    AUDIO = "audio"
    TRANSCRIPT = "transcript"
    OUTPUTS = "outputs"


class SessionProcessingState(SQLModel, table=True):
    """Workflow metadata for one Session, separate from its canonical artifacts.

    Draft transcript content stays in the Session folder. This record only identifies the
    source artifact it was based on and records navigation/error state, so it can never be
    mistaken for the completed reviewed transcript consumed by generation.
    """

    __tablename__ = "session_processing_state"
    __table_args__ = (
        CheckConstraint("phase in ('audio', 'transcript', 'outputs')", name="ck_session_processing_state_phase_valid"),
        CheckConstraint(
            "draft_source_artifact is null or draft_source_artifact in ('transcript', 'reviewed_transcript')",
            name="ck_session_processing_state_draft_source_valid",
        ),
        CheckConstraint(
            "(draft_source_artifact is null and draft_source_modified_ns is null) "
            "or (draft_source_artifact is not null and draft_source_modified_ns is not null and draft_source_modified_ns >= 0)",
            name="ck_session_processing_state_draft_source_complete",
        ),
        CheckConstraint(
            "failed_phase is null or failed_phase in ('audio', 'transcript', 'outputs')",
            name="ck_session_processing_state_failed_phase_valid",
        ),
    )

    session_id: uuid.UUID = Field(primary_key=True, foreign_key="session.id", ondelete="CASCADE")
    phase: str = Field(default=SessionProcessingPhase.AUDIO.value)
    draft_source_artifact: str | None = Field(default=None)
    draft_source_modified_ns: int | None = Field(default=None)
    failed_phase: str | None = Field(default=None)
    failure_message: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
