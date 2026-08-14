from __future__ import annotations

import shutil
from pathlib import Path

from .. import _paths
from ..model.cast import Player, PlayerSet
from .player_set_io import load_player_set, save_player_set
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


def delete_player(campaign_slug: str, player_slug: str) -> None:
    current = load_player_set(campaign_slug)
    remaining = tuple(p for p in current.players if p.slug != player_slug)
    save_player_set(campaign_slug, PlayerSet(players=remaining))


def cleanup_orphan_player_dirs(campaign_slug: str) -> tuple[str, ...]:
    root = _paths.players_dir(campaign_slug)
    if not root.exists():
        return ()
    known = {p.slug for p in load_player_set(campaign_slug).players}
    deleted: list[str] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name not in known:
            shutil.rmtree(child)
            deleted.append(child.name)
    return tuple(deleted)
