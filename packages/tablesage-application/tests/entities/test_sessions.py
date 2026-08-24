from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from tablesage_application import Application
from tablesage_model.model import GAME_MASTER_ROLE, Campaign, Player


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

    # directly exercise that the next sequence is max()+1, not count()+1
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


def test_session_folder_would_collide_reflects_disk_state(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    assert application.session_folder_would_collide(campaign.id) is False

    game_session = application.create_session(campaign.id, "Session One")
    application.delete_session(game_session.id)

    # deleting the only session resets next_sequence_number back to 1, colliding with the orphaned "001" folder
    assert application.session_folder_would_collide(campaign.id) is True


def test_delete_colliding_session_folder_clears_a_stray_folder_left_by_delete(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    application.delete_session(game_session.id)
    assert application.session_folder_would_collide(campaign.id) is True

    application.delete_colliding_session_folder(campaign.id)

    assert application.session_folder_would_collide(campaign.id) is False
    # the collision is now cleared, so creating a new session (reusing sequence 1) succeeds
    recreated = application.create_session(campaign.id, "Session One (again)")
    assert recreated.sequence_number == 1


def test_create_session_raises_friendly_error_on_uncleared_collision(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    application.delete_session(game_session.id)

    with pytest.raises(ValueError, match="already exists on disk"):
        application.create_session(campaign.id, "Session One (again)")


def test_get_session_raises_for_unknown_id(tmp_path: Path) -> None:
    application = Application(tmp_path)

    with pytest.raises(ValueError, match="not found"):
        application.get_session(Campaign(name="whatever").id)


def test_update_session_changes_name_and_date_no_fs_side_effect(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    updated = application.update_session(game_session.id, "Session One (renamed)", date(2026, 3, 1))

    assert updated.name == "Session One (renamed)"
    assert updated.session_date == date(2026, 3, 1)
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001").is_dir()


def test_delete_session_removes_row_but_keeps_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    application.delete_session(game_session.id)

    assert application.list_sessions(campaign.id) == []
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001").is_dir()


def test_create_session_seeds_attendance_from_roster_when_first_session(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    gm = application.create_player(Player(name="Gary"))
    application.add_player_to_campaign(campaign.id, gm.id, GAME_MASTER_ROLE)
    character = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, character.id, "Zaria the Bold")

    game_session = application.create_session(campaign.id, "Session One")

    attendance = application.list_attendance(game_session.id)
    assert {(a.player_id, a.roles) for a in attendance} == {(gm.id, ("Game Master",)), (character.id, ("Zaria the Bold",))}


def test_create_session_seeds_attendance_from_previous_session_when_one_exists(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    gm = application.create_player(Player(name="Gary"))
    application.add_player_to_campaign(campaign.id, gm.id, GAME_MASTER_ROLE)
    character = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, character.id, "Zaria the Bold")

    first = application.create_session(campaign.id, "Session One")
    # session one auto-seeded from the roster; drop the character so only the GM attended
    character_attendee = next(a for a in application.list_attendance(first.id) if a.player_id == character.id)
    application.remove_attendance(first.id, character_attendee.attendance_id)
    gm_attendee = next(a for a in application.list_attendance(first.id) if a.player_id == gm.id)
    application.set_attendance_roles(first.id, gm_attendee.attendance_id, ["Game Master", "Narrator"])

    second = application.create_session(campaign.id, "Session Two")

    attendance = application.list_attendance(second.id)
    assert [(a.player_id, a.roles) for a in attendance] == [(gm.id, ("Game Master", "Narrator"))]


def test_create_session_skips_previous_attendees_removed_from_roster(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    membership = application.add_player_to_campaign(campaign.id, player.id, "Zaria")

    # session one auto-seeds "Alice" as an attendee from the roster
    application.create_session(campaign.id, "Session One")
    application.remove_from_roster(membership.id)

    second = application.create_session(campaign.id, "Session Two")

    assert application.list_attendance(second.id) == []


def test_add_attendance_seeds_role_translating_game_master(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    gm = application.create_player(Player(name="Gary"))
    application.add_player_to_campaign(campaign.id, gm.id, GAME_MASTER_ROLE)
    character = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, character.id, "Zaria the Bold")

    gm_attendee = application.add_attendance(game_session.id, gm.id)
    character_attendee = application.add_attendance(game_session.id, character.id)

    assert gm_attendee.roles == ("Game Master",)
    assert character_attendee.roles == ("Zaria the Bold",)


def test_add_attendance_rejects_non_roster_player(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))

    with pytest.raises(ValueError, match="not a member of the campaign roster"):
        application.add_attendance(game_session.id, player.id)


def test_add_attendance_rejects_duplicate(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Alice's Character")
    application.add_attendance(game_session.id, player.id)

    with pytest.raises(ValueError, match="already attending"):
        application.add_attendance(game_session.id, player.id)


def test_remove_attendance_removes_row(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Alice's Character")
    attendee = application.add_attendance(game_session.id, player.id)

    application.remove_attendance(game_session.id, attendee.attendance_id)

    assert application.list_attendance(game_session.id) == []


def test_set_attendance_roles_replaces_full_set(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    attendee = application.add_attendance(game_session.id, player.id)

    updated = application.set_attendance_roles(game_session.id, attendee.attendance_id, ["Zaria the Bold", "Narrator"])

    assert updated.roles == ("Zaria the Bold", "Narrator")


def test_set_attendance_roles_rejects_empty_list(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    attendee = application.add_attendance(game_session.id, player.id)

    with pytest.raises(ValueError, match="At least one role"):
        application.set_attendance_roles(game_session.id, attendee.attendance_id, ["   "])
