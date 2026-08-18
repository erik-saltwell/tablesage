from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class SessionAttendance(SQLModel, table=True):
    """Joins a campaign-roster player to a session.

    Only players who are members of the session's campaign (via
    ``CampaignPlayer``) should be added here; that rule is enforced at the
    application layer, not the database.
    """

    __tablename__ = "session_attendance"
    __table_args__ = (UniqueConstraint("session_id", "player_id", name="uq_session_attendance_session_id_player_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="session.id", ondelete="CASCADE")
    player_id: uuid.UUID = Field(foreign_key="player.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
