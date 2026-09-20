from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class SessionAttendance(SQLModel, table=True):
    """Joins a workspace-wide player to a session."""

    __tablename__ = "session_attendance"
    __table_args__ = (UniqueConstraint("session_id", "player_id", name="uq_session_attendance_session_id_player_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="session.id", ondelete="CASCADE")
    player_id: uuid.UUID = Field(foreign_key="player.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
