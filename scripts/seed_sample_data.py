"""Fill a TableSage database with sample data for manual testing.

Usage (from the repo root, inside the venv):

    python scripts/seed_sample_data.py            # seed .tablesage/ in the current directory
    python scripts/seed_sample_data.py --reset     # wipe .tablesage/ first, then seed fresh
    python scripts/seed_sample_data.py --cwd /tmp/scratch   # seed somewhere else

Safe to re-run without --reset: campaigns/players that already exist (by name)
are reused rather than recreated, so you won't get duplicate-name errors.
"""

from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path

from tablesage_application import Application
from tablesage_model.model import Campaign, GlossaryEntry, Player


def _get_or_create_campaign(app: Application, name: str, *, description: str | None = None, game_system: str | None = None) -> Campaign:
    for campaign in app.list_campaigns():
        if campaign.name == name:
            return campaign
    return app.create_campaign(Campaign(name=name, description=description, game_system=game_system))


def _get_or_create_player(app: Application, name: str) -> Player:
    for player in app.list_players():
        if player.name == name:
            return player
    return app.create_player(Player(name=name))


def _ensure_roster(app: Application, campaign: Campaign, player: Player, default_role_name: str) -> None:
    existing = {p.id for _, p in app.list_roster(campaign.id)}
    if player.id in existing:
        return
    app.add_player_to_campaign(campaign.id, player.id, default_role_name)


def _ensure_glossary_entry(app: Application, campaign: Campaign, term: str, description: str) -> None:
    existing = {entry.term for entry in app.list_glossary_entries(campaign.id)}
    if term in existing:
        return
    app.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term=term, description=description))


def _ensure_sessions(app: Application, campaign: Campaign, sessions: list[tuple[str, date]]) -> None:
    existing_names = {s.name for s in app.list_sessions(campaign.id)}
    for name, session_date in sessions:
        if name in existing_names:
            continue
        app.create_session(campaign.id, name, session_date)


def seed(app: Application) -> None:
    alice = _get_or_create_player(app, "Alice")
    bob = _get_or_create_player(app, "Bob")
    priya = _get_or_create_player(app, "Priya")
    sam = _get_or_create_player(app, "Sam")

    # A player with no voice clips/centroid yet, to exercise that empty state.
    _get_or_create_player(app, "Jordan")

    iron_pact = _get_or_create_campaign(
        app,
        "Iron Pact",
        description="Dwarven holds under siege from below.",
        game_system="Pathfinder 2e",
    )
    ashen_crown = _get_or_create_campaign(
        app,
        "Ashen Crown",
        description="A cursed throne, and everyone who wants it.",
        game_system="D&D 5e",
    )
    voidfall = _get_or_create_campaign(
        app,
        "Voidfall",
        description="Heist crew in a dying star system.",
        game_system="Blades in the Dark",
    )
    # A campaign with no roster/sessions/glossary yet, to exercise that empty state.
    _get_or_create_campaign(app, "New Campaign (Empty)")

    _ensure_roster(app, iron_pact, alice, "game-master")
    _ensure_roster(app, iron_pact, bob, "Thorgrim")
    _ensure_roster(app, iron_pact, priya, "Lyra")

    _ensure_roster(app, ashen_crown, bob, "game-master")
    _ensure_roster(app, ashen_crown, sam, "Kestrel")
    _ensure_roster(app, ashen_crown, priya, "Nadia")

    _ensure_roster(app, voidfall, priya, "game-master")
    _ensure_roster(app, voidfall, alice, "Vex")
    _ensure_roster(app, voidfall, sam, "Juno")

    _ensure_glossary_entry(app, iron_pact, "Ironhold", "The dwarven capital city, built into the Ashspine range.")
    _ensure_glossary_entry(app, iron_pact, "The Sundering", "The cataclysm that split the continent centuries ago.")
    _ensure_glossary_entry(app, ashen_crown, "The Crownless King", "A legendary tyrant said to still haunt the throne room.")

    _ensure_sessions(
        app,
        iron_pact,
        [
            ("The Descent Begins", date(2026, 1, 4)),
            ("Tunnels of the Deep Kin", date(2026, 1, 11)),
            ("The Ashspine Betrayal", date(2026, 1, 25)),
        ],
    )
    _ensure_sessions(
        app,
        ashen_crown,
        [
            ("A Crown Without a Head", date(2026, 2, 1)),
            ("The Regent's Gambit", date(2026, 2, 15)),
        ],
    )
    _ensure_sessions(app, voidfall, [("The Long Fall", date(2026, 3, 1))])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--cwd",
        type=Path,
        default=Path.cwd(),
        help="Directory whose .tablesage/ should be seeded (default: current directory).",
    )
    parser.add_argument("--reset", action="store_true", help="Delete .tablesage/ under --cwd before seeding.")
    args = parser.parse_args()

    if args.reset:
        tablesage_dir = args.cwd / ".tablesage"
        if tablesage_dir.exists():
            shutil.rmtree(tablesage_dir)
            print(f"Removed {tablesage_dir}")

    app = Application(args.cwd)
    seed(app)

    print(f"Seeded sample data into {args.cwd / '.tablesage'}")
    print(f"Campaigns: {[c.name for c in app.list_campaigns()]}")
    print(f"Players:   {[p.name for p in app.list_players()]}")


if __name__ == "__main__":
    main()
