from __future__ import annotations

import json
import uuid
import wave
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from tablesage_model.model import Player
from tablesage_tools.embeddings import Embedding, compute_centroid

from ._fs import cleanup_orphan_dirs, create_named_entity_folder, rename_named_entity

VOICE_CLIP_GLOB = "*.wav"


@dataclass(frozen=True)
class VoiceClip:
    """A voice clip file on disk. Has no database row of its own."""

    filename: str
    duration_seconds: float


def create_player(session: Session, player: Player, players_root: Path) -> Player:
    session.add(player)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(f"A player named '{player.name}' already exists.") from exc

    try:
        create_named_entity_folder(players_root, player.name, kind="player")
    except ValueError:
        session.rollback()
        raise

    return player


def list_players(session: Session) -> list[Player]:
    return list(session.exec(select(Player)).all())


def get_player(session: Session, player_id: uuid.UUID) -> Player:
    player = session.get(Player, player_id)
    if player is None:
        raise ValueError("Player not found.")
    return player


def rename_player(session: Session, player_id: uuid.UUID, new_name: str, players_root: Path) -> Player:
    player = get_player(session, player_id)
    rename_named_entity(session, player, new_name, players_root, kind="player")
    return player


def delete_player(session: Session, player_id: uuid.UUID) -> None:
    player = get_player(session, player_id)
    session.delete(player)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("This player has attended sessions and cannot be deleted.") from exc


def cleanup_orphan_player_dirs(session: Session, players_root: Path) -> list[str]:
    known_names = {player.name for player in list_players(session)}
    return cleanup_orphan_dirs(players_root, known_names)


def list_voice_clips(player_folder: Path) -> list[VoiceClip]:
    """List voice clip files in a player's folder. The filesystem is the source of truth here — there is no voice-sample table."""
    if not player_folder.exists():
        return []
    return [
        VoiceClip(filename=path.name, duration_seconds=_wav_duration_seconds(path)) for path in sorted(player_folder.glob(VOICE_CLIP_GLOB))
    ]


def _wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wav_file:
        rate = wav_file.getframerate()
        return wav_file.getnframes() / float(rate) if rate else 0.0


def _serialize_centroid(embedding: Embedding) -> tuple[str, int]:
    return json.dumps(list(embedding.root)), len(embedding.root)


def recompute_centroid(session: Session, player_id: uuid.UUID, player_folder: Path, embed: Callable[[Path], Embedding]) -> Player:
    """Recompute a player's centroid from every clip currently on disk.

    Always a full recompute (re-embeds everything), never incremental. Clears
    the centroid entirely rather than leaving a stale one if no clips remain.
    """
    player = get_player(session, player_id)
    clip_paths = sorted(player_folder.glob(VOICE_CLIP_GLOB)) if player_folder.exists() else []

    if not clip_paths:
        player.centroid_embedding = None
        player.embedding_dimension = None
        player.sample_count = 0
        player.computed_at = None
    else:
        centroid = compute_centroid([embed(path) for path in clip_paths])
        serialized, dimension = _serialize_centroid(centroid)
        player.centroid_embedding = serialized
        player.embedding_dimension = dimension
        player.sample_count = len(clip_paths)
        player.computed_at = datetime.now(UTC)

    session.add(player)
    session.flush()
    return player


def delete_voice_clip(
    session: Session, player_id: uuid.UUID, filename: str, player_folder: Path, embed: Callable[[Path], Embedding]
) -> Player:
    """Delete a voice clip file, then auto-recompute the centroid over what remains."""
    clip_path = player_folder / filename
    if not clip_path.is_file():
        raise ValueError(f"Voice clip '{filename}' not found.")
    clip_path.unlink()
    return recompute_centroid(session, player_id, player_folder, embed)
