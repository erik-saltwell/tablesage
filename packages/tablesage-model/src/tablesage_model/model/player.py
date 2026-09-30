from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel

from ..player_names import validate_player_name


class Player(SQLModel, table=True):
    """A top-level participant identity, independent of any campaign.

    A player carries its own voice print directly (voice print fields) rather
    than through a separate table, since a player has at most one current
    voice print and no voice print history is tracked.
    """

    __table_args__ = (CheckConstraint("trim(name) != ''", name="ck_player_name_non_blank"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True)
    voice_print_embedding: str | None = Field(default=None)
    embedding_dimension: int | None = Field(default=None)
    sample_count: int = Field(default=0)
    computed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        return validate_player_name(value)
