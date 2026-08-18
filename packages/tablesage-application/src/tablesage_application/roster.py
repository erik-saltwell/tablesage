from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from tablesage_model.model import CampaignPlayer, Player


def add_player_to_campaign(session: Session, campaign_id: uuid.UUID, player_id: uuid.UUID, default_role_name: str) -> CampaignPlayer:
    membership = CampaignPlayer(campaign_id=campaign_id, player_id=player_id, default_role_name=default_role_name)
    session.add(membership)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("This player is already on the campaign roster.") from exc
    return membership


def list_roster(session: Session, campaign_id: uuid.UUID) -> list[tuple[CampaignPlayer, Player]]:
    rows = session.exec(
        select(CampaignPlayer, Player).where(CampaignPlayer.campaign_id == campaign_id).where(CampaignPlayer.player_id == Player.id)
    ).all()
    return list(rows)


def update_default_role(session: Session, membership_id: uuid.UUID, default_role_name: str) -> CampaignPlayer:
    membership = session.get(CampaignPlayer, membership_id)
    if membership is None:
        raise ValueError("Roster membership not found.")
    membership.default_role_name = default_role_name
    session.flush()
    return membership


def remove_from_roster(session: Session, membership_id: uuid.UUID) -> None:
    membership = session.get(CampaignPlayer, membership_id)
    if membership is None:
        raise ValueError("Roster membership not found.")
    session.delete(membership)
