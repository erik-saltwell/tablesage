from __future__ import annotations

from pathlib import Path


def campaigns_root(cwd: Path) -> Path:
    return cwd / ".tablesage" / "campaigns"


def players_root(cwd: Path) -> Path:
    return cwd / ".tablesage" / "players"


def campaign_folder(cwd: Path, campaign_name: str) -> Path:
    return campaigns_root(cwd) / campaign_name


def player_folder(cwd: Path, player_name: str) -> Path:
    return players_root(cwd) / player_name


def session_folder(cwd: Path, campaign_name: str, sequence_number: int) -> Path:
    return campaign_folder(cwd, campaign_name) / f"{sequence_number:03d}"
