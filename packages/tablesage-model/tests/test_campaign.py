from __future__ import annotations

from pathlib import Path

import pytest
import tablesage_model
from alembic import command
from alembic.config import Config
from sqlmodel import Session, create_engine, select
from tablesage_model.model import Campaign

MIGRATIONS_DIR = Path(tablesage_model.__file__).parent / "_migrations"


def _upgrade_head(db_path: Path) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(config, "head")


def test_migration_creates_campaign_table_and_round_trips(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    _upgrade_head(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        campaign = Campaign(name="Iron Pact")
        session.add(campaign)
        session.commit()

        stored = session.exec(select(Campaign).where(Campaign.id == campaign.id)).one()

    assert stored.name == "Iron Pact"
    assert stored.description is None
    assert stored.game_system is None
    assert stored.default_gm_name is None
    assert stored.created_at is not None
    assert stored.updated_at is not None


def test_campaign_rejects_blank_name() -> None:
    with pytest.raises(ValueError, match="name must not be blank"):
        Campaign(name="   ")
