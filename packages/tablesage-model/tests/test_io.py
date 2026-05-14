from __future__ import annotations

from datetime import date
from pathlib import Path

from tablesage_model.io import (
    load_campaign,
    load_campaign_set,
    load_player,
    load_player_set,
    load_session,
    load_session_set,
    save_campaign,
    save_campaign_set,
    save_player,
    save_player_set,
    save_session,
    save_session_set,
)
from tablesage_model.model.campaign import Campaign, CampaignSet, Session, SessionSet
from tablesage_model.model.campaign.campaign_set import CampaignName
from tablesage_model.model.campaign.session_set import SessionName
from tablesage_model.model.cast import Embedding, Player, PlayerName, PlayerSet, Role, VoiceSample


def test_campaign_set_round_trips() -> None:
    campaign_set = CampaignSet(campaigns=(CampaignName(slug="sable-crown", name="Sable Crown"),))

    save_campaign_set(campaign_set)

    assert load_campaign_set() == campaign_set


def test_campaign_round_trips() -> None:
    campaign = Campaign(
        slug="sable-crown",
        name="Sable Crown",
        default_gm="Ada",
        players={
            "ada": (Role(name="Game Master"),),
            "bryn": (Role(name="Paladin"), Role(name="Archivist")),
        },
    )

    save_campaign(campaign)

    assert load_campaign(campaign.slug) == campaign


def test_player_set_round_trips() -> None:
    player_set = PlayerSet(players=(PlayerName(slug="ada", name="Ada"), PlayerName(slug="bryn", name="Bryn")))

    save_player_set("sable-crown", player_set)

    assert load_player_set("sable-crown") == player_set


def test_player_round_trips() -> None:
    player = Player(
        slug="ada",
        name="Ada",
        voice_samples=(
            VoiceSample(filepath=Path("voice_clips/ada-1.wav"), embedding=Embedding(root=(0.1, 0.2, 0.3))),
            VoiceSample(filepath=Path("voice_clips/ada-2.wav"), embedding=Embedding(root=(0.4, 0.5, 0.6))),
        ),
        centroid=Embedding(root=(0.25, 0.35, 0.45)),
    )

    save_player("sable-crown", player)

    assert load_player("sable-crown", player.slug) == player


def test_session_set_round_trips() -> None:
    session_set = SessionSet(sessions=(SessionName(slug="session-one", name="Session One"),))

    save_session_set("sable-crown", session_set)

    assert load_session_set("sable-crown") == session_set


def test_session_round_trips() -> None:
    session = Session(
        session_date=date(2026, 5, 13),
        name="Session One",
        slug="session-one",
        attendees={
            "ada": (Role(name="Game Master"),),
            "bryn": (Role(name="Paladin"),),
        },
    )

    save_session("sable-crown", session)

    assert load_session("sable-crown", session.slug) == session
