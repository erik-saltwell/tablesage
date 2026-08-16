from __future__ import annotations

from sqlmodel import Session, select
from tablesage_model.model import Campaign


def has_campaigns(session: Session) -> bool:
    return session.exec(select(Campaign)).first() is not None


def create_campaign(session: Session, campaign: Campaign) -> Campaign:
    session.add(campaign)
    return campaign
