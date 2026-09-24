from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class SessionProcessingState(SQLModel, table=True):
    """Where a Session's saved Review Transcript draft came from, separate from its canonical artifacts.

    Draft transcript content stays in the Session folder. This record only identifies the source
    artifact it was based on (and that file's modification time), so a draft can never be mistaken
    for the completed reviewed transcript and is dropped once its source changes.
    """

    __tablename__ = "session_processing_state"
    __table_args__ = (
        CheckConstraint(
            "draft_source_artifact is null or draft_source_artifact in ('spellchecked_transcript', 'reviewed_transcript')",
            name="ck_session_processing_state_draft_source_valid",
        ),
        CheckConstraint(
            "(draft_source_artifact is null and draft_source_modified_ns is null) "
            "or (draft_source_artifact is not null and draft_source_modified_ns is not null and draft_source_modified_ns >= 0)",
            name="ck_session_processing_state_draft_source_complete",
        ),
    )

    session_id: uuid.UUID = Field(primary_key=True, foreign_key="session.id", ondelete="CASCADE")
    draft_source_artifact: str | None = Field(default=None)
    draft_source_modified_ns: int | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
