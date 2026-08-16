from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel


class Campaign(SQLModel, table=True):
    __table_args__ = (CheckConstraint("trim(name) != ''", name="ck_campaign_name_non_blank"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: str | None = Field(default=None)
    game_system: str | None = Field(default=None)
    default_gm_name: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be blank")
        return value
