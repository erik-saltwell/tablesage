from __future__ import annotations

from pathlib import Path

from sqlmodel import Session
from tablesage_model import setup
from tablesage_model.model import Campaign

from . import campaigns


class Application:
    def __init__(self, cwd: Path | None = None) -> None:
        self._db_path: Path = setup.ensure_database(cwd)
        self._engine = setup.create_engine(self._db_path)

    def has_campaigns(self) -> bool:
        with Session(self._engine) as session:
            return campaigns.has_campaigns(session)

    def create_campaign(self, campaign: Campaign) -> Campaign:
        with Session(self._engine) as session:
            result = campaigns.create_campaign(session, campaign)
            session.commit()
            session.refresh(result)
            return result
