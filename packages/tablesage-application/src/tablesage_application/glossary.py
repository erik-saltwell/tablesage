from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from tablesage_model.model import GlossaryEntry


def create_glossary_entry(session: Session, entry: GlossaryEntry) -> GlossaryEntry:
    session.add(entry)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(f"A glossary term '{entry.term}' already exists in this campaign.") from exc
    return entry


def list_glossary_entries(session: Session, campaign_id: uuid.UUID) -> list[GlossaryEntry]:
    return list(session.exec(select(GlossaryEntry).where(GlossaryEntry.campaign_id == campaign_id)).all())


def update_glossary_entry(
    session: Session, campaign_id: uuid.UUID, entry_id: uuid.UUID, term: str, description: str | None
) -> GlossaryEntry:
    entry = session.get(GlossaryEntry, (campaign_id, entry_id))
    if entry is None:
        raise ValueError("Glossary entry not found.")
    entry.term = term
    entry.description = description
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(f"A glossary term '{term}' already exists in this campaign.") from exc
    return entry


def delete_glossary_entry(session: Session, campaign_id: uuid.UUID, entry_id: uuid.UUID) -> None:
    entry = session.get(GlossaryEntry, (campaign_id, entry_id))
    if entry is None:
        raise ValueError("Glossary entry not found.")
    session.delete(entry)
