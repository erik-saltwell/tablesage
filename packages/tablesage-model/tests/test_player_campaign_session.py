from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import tablesage_model
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session as DBSession
from sqlmodel import create_engine
from tablesage_model.model import (
    Campaign,
    CampaignPlayer,
    GlossaryEntry,
    Player,
    Session,
    SessionAttendance,
    SessionAttendanceRole,
    SessionStatus,
)

MIGRATIONS_DIR = Path(tablesage_model.__file__).parent / "_migrations"


def _upgrade_head(db_path: Path) -> None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(config, "head")


def test_player_has_no_campaign_dependency_and_unique_name(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    _upgrade_head(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    with DBSession(engine) as session:
        player = Player(name="Alice")
        session.add(player)
        session.commit()
        session.refresh(player)

        assert player.centroid_embedding is None
        assert player.sample_count == 0

        session.add(Player(name="Alice"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_player_rejects_blank_name() -> None:
    with pytest.raises(ValueError, match="name must not be blank"):
        Player(name="   ")


def test_campaign_player_links_and_default_role(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    _upgrade_head(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    with DBSession(engine) as session:
        campaign = Campaign(name="Iron Pact")
        player = Player(name="Alice")
        session.add(campaign)
        session.add(player)
        session.commit()
        session.refresh(campaign)
        session.refresh(player)

        membership = CampaignPlayer(campaign_id=campaign.id, player_id=player.id, default_role_name="game-master")
        session.add(membership)
        session.commit()

        # same player can join a second campaign with a different default role
        other_campaign = Campaign(name="Second Campaign")
        session.add(other_campaign)
        session.commit()
        session.refresh(other_campaign)

        session.add(CampaignPlayer(campaign_id=other_campaign.id, player_id=player.id, default_role_name="Thorgrim"))
        session.commit()

        # duplicate (campaign, player) pair is rejected
        session.add(CampaignPlayer(campaign_id=campaign.id, player_id=player.id, default_role_name="Someone Else"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_glossary_entry_scoped_and_unique_term_per_campaign(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    _upgrade_head(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    with DBSession(engine) as session:
        campaign_a = Campaign(name="Campaign A")
        campaign_b = Campaign(name="Campaign B")
        session.add(campaign_a)
        session.add(campaign_b)
        session.commit()
        session.refresh(campaign_a)
        session.refresh(campaign_b)

        session.add(GlossaryEntry(campaign_id=campaign_a.id, term="Ironhold", description="Capital city"))
        session.commit()

        # same term is fine in a different campaign
        session.add(GlossaryEntry(campaign_id=campaign_b.id, term="Ironhold"))
        session.commit()

        # duplicate term within the same campaign is rejected
        session.add(GlossaryEntry(campaign_id=campaign_a.id, term="Ironhold"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_session_sequence_number_unique_per_campaign(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    _upgrade_head(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    with DBSession(engine) as session:
        campaign = Campaign(name="Iron Pact")
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

        first = Session(campaign_id=campaign.id, sequence_number=1, name="Session One", session_date=date(2026, 1, 1))
        session.add(first)
        session.commit()
        session.refresh(first)

        assert first.status == SessionStatus.DRAFT.value

        session.add(Session(campaign_id=campaign.id, sequence_number=1, name="Duplicate"))
        with pytest.raises(IntegrityError):
            session.commit()


def test_session_attendance_and_roles(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    _upgrade_head(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    with DBSession(engine) as session:
        campaign = Campaign(name="Iron Pact")
        player = Player(name="Alice")
        session.add(campaign)
        session.add(player)
        session.commit()
        session.refresh(campaign)
        session.refresh(player)

        game_session = Session(campaign_id=campaign.id, sequence_number=1, name="Session One")
        session.add(game_session)
        session.commit()
        session.refresh(game_session)

        attendance = SessionAttendance(session_id=game_session.id, player_id=player.id)
        session.add(attendance)
        session.commit()
        session.refresh(attendance)

        session.add(SessionAttendanceRole(attendance_id=attendance.id, name="Game Master"))
        session.commit()

        # a player can hold more than one role in the same session
        session.add(SessionAttendanceRole(attendance_id=attendance.id, name="Narrator NPC"))
        session.commit()

        # the same role name twice for the same attendee is rejected
        session.add(SessionAttendanceRole(attendance_id=attendance.id, name="Game Master"))
        with pytest.raises(IntegrityError):
            session.commit()
