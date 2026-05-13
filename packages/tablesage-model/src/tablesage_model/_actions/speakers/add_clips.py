from __future__ import annotations

from pathlib import Path

# def _add_clip(campaign_slug: str, clip_path: Path, player: Player) -> Player:
#     player_dir = _paths.player_dir(campaign_slug, player.slug)


def add_clips(clip_directory: Path) -> None:
    if not clip_directory.is_dir():
        msg = f"Cannot add clips from {clip_directory} because it is not a directory"
        raise ValueError(msg)
    if not clip_directory.exists():
        msg = f"Cannot add clips from {clip_directory} because it does not exist"
        raise ValueError(msg)
