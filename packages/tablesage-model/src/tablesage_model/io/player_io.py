from __future__ import annotations

from pathlib import Path

from .. import _paths
from ..model.cast import Player
from .yaml_io import load_model_from_yaml, save_model_to_yaml


def load_player(campaign_slug: str, player_slug: str) -> Player:
    file_path: Path = _paths.player_file(campaign_slug, player_slug)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if not file_path.is_file():
        raise IsADirectoryError(file_path)
    player = load_model_from_yaml(file_path, Player)
    if player.slug != player_slug:
        raise ValueError(f"Slug mismatch: directory is '{player_slug}', file says '{player.slug}'")
    return player


def save_player(campaign_slug: str, player: Player) -> None:
    file_path: Path = _paths.player_file(campaign_slug, player.slug)
    if file_path.is_dir():
        raise IsADirectoryError(file_path)
    save_model_to_yaml(file_path, player)
