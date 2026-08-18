from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel


class GlossaryEntry(SQLModel, table=True):
    """Campaign-specific terminology used as generation context.

    Glossary entries have no independent identity outside their owning
    campaign, so the campaign id is part of the primary key.
    """

    __tablename__ = "glossary_entry"
    __table_args__ = (
        UniqueConstraint("campaign_id", "term", name="uq_glossary_entry_campaign_id_term"),
        CheckConstraint("trim(term) != ''", name="ck_glossary_entry_term_non_blank"),
    )

    campaign_id: uuid.UUID = Field(foreign_key="campaign.id", ondelete="CASCADE", primary_key=True)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    term: str
    description: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validates("term")
    def validate_term(self, key: str, value: str) -> str:
        if not value.strip():
            raise ValueError("term must not be blank")
        return value
