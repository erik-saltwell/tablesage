from __future__ import annotations

from pathlib import Path

import pytest
from tablesage_application import Application
from tablesage_model.model import Campaign, Player


def test_add_player_to_campaign_and_list_roster(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))

    membership = application.add_player_to_campaign(campaign.id, player.id, "game-master")

    roster = application.list_roster(campaign.id)
    assert len(roster) == 1
    stored_membership, stored_player = roster[0]
    assert stored_membership.id == membership.id
    assert stored_player.name == "Alice"
    assert stored_membership.default_role_name == "game-master"


def test_same_player_can_have_different_roles_in_different_campaigns(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign_a = application.create_campaign(Campaign(name="Campaign A"))
    campaign_b = application.create_campaign(Campaign(name="Campaign B"))
    player = application.create_player(Player(name="Alice"))

    application.add_player_to_campaign(campaign_a.id, player.id, "game-master")
    application.add_player_to_campaign(campaign_b.id, player.id, "Thorgrim")

    role_in_a = application.list_roster(campaign_a.id)[0][0].default_role_name
    role_in_b = application.list_roster(campaign_b.id)[0][0].default_role_name
    assert role_in_a == "game-master"
    assert role_in_b == "Thorgrim"


def test_add_player_to_campaign_rejects_duplicate_membership(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "game-master")

    with pytest.raises(ValueError, match="already"):
        application.add_player_to_campaign(campaign.id, player.id, "Someone Else")


def test_update_default_role(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    membership = application.add_player_to_campaign(campaign.id, player.id, "game-master")

    updated = application.update_default_role(membership.id, "Thorgrim")

    assert updated.default_role_name == "Thorgrim"


def test_remove_from_roster_does_not_delete_player(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    membership = application.add_player_to_campaign(campaign.id, player.id, "game-master")

    application.remove_from_roster(membership.id)

    assert application.list_roster(campaign.id) == []
    assert application.get_player(player.id).name == "Alice"
