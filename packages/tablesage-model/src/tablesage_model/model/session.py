from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel


class SessionStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    PROCESSING = "processing"
    PROCESSED = "processed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class Session(SQLModel, table=True):
    """A dated recording and its processing lifecycle within a campaign.

    ``sequence_number`` is assigned as ``max existing + 1`` at creation, is
    never reused after a session is deleted, and is the on-disk session
    folder name (zero-padded to 3 digits).
    """

    __tablename__ = "session"
    __table_args__ = (
        UniqueConstraint("campaign_id", "sequence_number", name="uq_session_campaign_id_sequence_number"),
        CheckConstraint("trim(name) != ''", name="ck_session_name_non_blank"),
        CheckConstraint(
            "status in ('draft', 'ready', 'processing', 'processed', 'needs_review', 'failed')",
            name="ck_session_status_valid",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    campaign_id: uuid.UUID = Field(foreign_key="campaign.id", ondelete="CASCADE")
    sequence_number: int
    name: str
    session_date: date | None = Field(default=None)
    # Stored as plain text (not a SQLAlchemy Enum column) so the on-disk value
    # is the readable SessionStatus value ("draft", ...) rather than the
    # member name SQLAlchemy's Enum type would store by default ("DRAFT").
    status: str = Field(default=SessionStatus.DRAFT.value)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value
