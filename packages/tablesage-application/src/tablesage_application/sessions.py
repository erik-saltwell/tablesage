from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import func
from sqlmodel import Session, select
from tablesage_model.model import Session as GameSession

from ._fs import cleanup_orphan_dirs


def create_session(session: Session, campaign_id: uuid.UUID, name: str, session_date: date | None, campaign_folder: Path) -> GameSession:
    max_sequence = session.exec(select(func.max(GameSession.sequence_number)).where(GameSession.campaign_id == campaign_id)).one()
    next_sequence = (max_sequence or 0) + 1

    game_session = GameSession(campaign_id=campaign_id, sequence_number=next_sequence, name=name, session_date=session_date)
    session.add(game_session)
    session.flush()

    folder = campaign_folder / f"{next_sequence:03d}"
    folder.mkdir(parents=True, exist_ok=False)

    return game_session


def list_sessions(session: Session, campaign_id: uuid.UUID) -> list[GameSession]:
    return list(session.exec(select(GameSession).where(GameSession.campaign_id == campaign_id)).all())


def cleanup_orphan_session_dirs(session: Session, campaign_id: uuid.UUID, campaign_folder: Path) -> list[str]:
    known_names = {f"{game_session.sequence_number:03d}" for game_session in list_sessions(session, campaign_id)}
    return cleanup_orphan_dirs(campaign_folder, known_names)
