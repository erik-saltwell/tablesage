from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel


class SessionAttendanceRole(SQLModel, table=True):
    """Allows one session attendee to have zero or more free-form roles.

    Seeded from the matching ``CampaignPlayer.default_role_name`` when
    attendance is created; the user may add, edit, or remove roles after.
    """

    __tablename__ = "session_attendance_role"
    __table_args__ = (
        UniqueConstraint("attendance_id", "name", name="uq_session_attendance_role_attendance_id_name"),
        CheckConstraint("trim(name) != ''", name="ck_session_attendance_role_name_non_blank"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    attendance_id: uuid.UUID = Field(foreign_key="session_attendance.id", ondelete="CASCADE")
    name: str

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value
