from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from tablesage_model.model import Campaign
from tablesage_model.model import Session as GameSession

from ._fs import cleanup_orphan_dirs, create_named_entity_folder, rename_named_entity


def has_campaigns(session: Session) -> bool:
    return session.exec(select(Campaign)).first() is not None


def create_campaign(session: Session, campaign: Campaign, campaigns_root: Path) -> Campaign:
    session.add(campaign)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(f"A campaign named '{campaign.name}' already exists.") from exc

    try:
        create_named_entity_folder(campaigns_root, campaign.name, kind="campaign")
    except ValueError:
        session.rollback()
        raise

    return campaign


def list_campaigns(session: Session) -> list[Campaign]:
    return list(session.exec(select(Campaign)).all())


def last_session_dates(session: Session) -> dict[uuid.UUID, date]:
    """Most recent session date per campaign id, computed dynamically from Session rows."""
    result: dict[uuid.UUID, date] = {}
    for game_session in session.exec(select(GameSession)).all():
        if game_session.session_date is None:
            continue
        current = result.get(game_session.campaign_id)
        if current is None or game_session.session_date > current:
            result[game_session.campaign_id] = game_session.session_date
    return result


def rename_campaign(session: Session, campaign_id: uuid.UUID, new_name: str, campaigns_root: Path) -> Campaign:
    campaign = session.get(Campaign, campaign_id)
    if campaign is None:
        raise ValueError("Campaign not found.")
    rename_named_entity(session, campaign, new_name, campaigns_root, kind="campaign")
    return campaign


def delete_campaign(session: Session, campaign_id: uuid.UUID) -> None:
    campaign = session.get(Campaign, campaign_id)
    if campaign is None:
        raise ValueError("Campaign not found.")
    session.delete(campaign)


def cleanup_orphan_campaign_dirs(session: Session, campaigns_root: Path) -> list[str]:
    known_names = {campaign.name for campaign in list_campaigns(session)}
    return cleanup_orphan_dirs(campaigns_root, known_names)
