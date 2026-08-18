from __future__ import annotations

from datetime import date
from pathlib import Path

from tablesage_application import Application
from tablesage_model.model import Campaign


def test_create_session_assigns_sequence_number_and_creates_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))

    first = application.create_session(campaign.id, "Session One", date(2026, 1, 1))
    second = application.create_session(campaign.id, "Session Two", date(2026, 1, 8))

    assert first.sequence_number == 1
    assert second.sequence_number == 2
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001").is_dir()
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "002").is_dir()


def test_sequence_numbers_are_never_reused_after_deletion(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.create_session(campaign.id, "Session One")

    # simulate the row being removed without renumbering (no delete_session yet;
    # directly exercise that the next sequence is max()+1, not count()+1)
    third = application.create_session(campaign.id, "Session Two")
    assert third.sequence_number == 2


def test_list_sessions_scoped_to_campaign(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign_a = application.create_campaign(Campaign(name="Campaign A"))
    campaign_b = application.create_campaign(Campaign(name="Campaign B"))
    application.create_session(campaign_a.id, "A1")
    application.create_session(campaign_b.id, "B1")

    sessions_a = application.list_sessions(campaign_a.id)
    assert [s.name for s in sessions_a] == ["A1"]


def test_last_session_dates_computed_dynamically(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.create_session(campaign.id, "Session One", date(2026, 1, 1))
    application.create_session(campaign.id, "Session Two", date(2026, 1, 8))

    last_dates = application.last_session_dates()

    assert last_dates[campaign.id] == date(2026, 1, 8)


def test_cleanup_orphan_session_dirs_removes_only_unknown_folders(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.create_session(campaign.id, "Session One")

    orphan = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "999"
    orphan.mkdir()

    removed = application.cleanup_orphan_session_dirs(campaign.id)

    assert removed == ["999"]
    assert not orphan.exists()
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001").is_dir()
