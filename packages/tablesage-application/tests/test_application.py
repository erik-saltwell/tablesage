from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from tablesage_application import Application
from tablesage_model.model import Campaign, GlossaryEntry, Player


def test_has_campaigns_is_false_for_a_fresh_database(tmp_path: Path) -> None:
    application = Application(tmp_path)

    assert application.has_campaigns() is False


def test_create_campaign_persists_and_returns_a_usable_campaign(tmp_path: Path) -> None:
    application = Application(tmp_path)

    created = application.create_campaign(Campaign(name="Iron Pact"))

    assert created.id is not None
    assert created.name == "Iron Pact"


def test_has_campaigns_is_true_after_creating_one(tmp_path: Path) -> None:
    application = Application(tmp_path)

    application.create_campaign(Campaign(name="Iron Pact"))

    assert application.has_campaigns() is True


def test_list_campaigns_returns_all_persisted_campaigns(tmp_path: Path) -> None:
    application = Application(tmp_path)
    application.create_campaign(Campaign(name="Iron Pact"))
    application.create_campaign(Campaign(name="Ashen Crown"))

    campaigns = application.list_campaigns()

    assert {campaign.name for campaign in campaigns} == {"Iron Pact", "Ashen Crown"}


def test_create_campaign_creates_a_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)

    application.create_campaign(Campaign(name="Iron Pact"))

    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact").is_dir()


def test_get_campaign_returns_the_matching_campaign(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))

    assert application.get_campaign(campaign.id).name == "Iron Pact"


def test_get_campaign_raises_for_unknown_id(tmp_path: Path) -> None:
    application = Application(tmp_path)

    with pytest.raises(ValueError, match="not found"):
        application.get_campaign(uuid.uuid4())


def test_update_campaign_sets_description_and_game_system(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))

    updated = application.update_campaign(campaign.id, "A grim war", "Dungeon World")

    assert updated.description == "A grim war"
    assert updated.game_system == "Dungeon World"
    assert application.get_campaign(campaign.id).description == "A grim war"


def test_rename_campaign_renames_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))

    renamed = application.rename_campaign(campaign.id, "Iron Pact Reforged")

    assert renamed.name == "Iron Pact Reforged"
    assert not (tmp_path / ".tablesage" / "campaigns" / "Iron Pact").exists()
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact Reforged").is_dir()


def test_rename_campaign_rejects_duplicate_name(tmp_path: Path) -> None:
    application = Application(tmp_path)
    application.create_campaign(Campaign(name="Iron Pact"))
    ashen_crown = application.create_campaign(Campaign(name="Ashen Crown"))

    with pytest.raises(ValueError, match="already exists"):
        application.rename_campaign(ashen_crown.id, "Iron Pact")


def test_delete_campaign_removes_row_but_keeps_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))

    application.delete_campaign(campaign.id)

    assert application.list_campaigns() == []
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact").is_dir()


def test_delete_campaign_cascades_to_roster_and_glossary(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "game-master")
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ironhold"))

    application.delete_campaign(campaign.id)

    # the player itself survives a campaign delete
    assert application.get_player(player.id).name == "Alice"


def test_cleanup_orphan_campaign_dirs_removes_only_unknown_folders(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.delete_campaign(campaign.id)
    application.create_campaign(Campaign(name="Ashen Crown"))

    removed = application.cleanup_orphan_campaign_dirs()

    assert removed == ["Iron Pact"]
    assert not (tmp_path / ".tablesage" / "campaigns" / "Iron Pact").exists()
    assert (tmp_path / ".tablesage" / "campaigns" / "Ashen Crown").is_dir()
