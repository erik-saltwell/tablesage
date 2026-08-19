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
from tablesage_tools.embeddings import DEFAULT_MIN_SAMPLE_SIMILARITY, DEFAULT_MIN_SAMPLES, Embedding, compute_centroid

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


def _compute_recompute_result(
    player_folder: Path,
    embed: Callable[[Path], Embedding],
    on_progress: Callable[[int, int], None] | None,
    min_sample_similarity: float,
    min_samples: int,
) -> tuple[Embedding | None, int, tuple[Path, ...]]:
    """Embed every clip on disk and compute the centroid, without touching the DB or filesystem.

    Returns the centroid (`None` if there are no clips), the count of clips
    that actually contributed to it, and every clip path that didn't
    (duplicates, pruned outliers) -- still present on disk either way.
    """
    clip_paths = sorted(player_folder.glob(VOICE_CLIP_GLOB)) if player_folder.exists() else []
    if not clip_paths:
        return None, 0, ()

    result = compute_centroid(clip_paths, embed, on_progress, min_sample_similarity, min_samples)
    used_count = len(clip_paths) - len(result.unused_paths)
    return result.centroid, used_count, result.unused_paths


def _apply_centroid(player: Player, centroid: Embedding | None, used_count: int) -> None:
    if centroid is None:
        player.centroid_embedding = None
        player.embedding_dimension = None
        player.sample_count = 0
        player.computed_at = None
    else:
        serialized, dimension = _serialize_centroid(centroid)
        player.centroid_embedding = serialized
        player.embedding_dimension = dimension
        player.sample_count = used_count
        player.computed_at = datetime.now(UTC)


def recompute_centroid(
    session: Session,
    player_id: uuid.UUID,
    player_folder: Path,
    embed: Callable[[Path], Embedding],
    on_progress: Callable[[int, int], None] | None = None,
    min_sample_similarity: float = DEFAULT_MIN_SAMPLE_SIMILARITY,
    min_samples: int = DEFAULT_MIN_SAMPLES,
) -> Player:
    """Recompute a player's centroid from every clip currently on disk.

    Always a full recompute (re-embeds everything), never incremental. Clears
    the centroid entirely rather than leaving a stale one if no clips remain.
    Duplicate clips (identical file contents) and similarity outliers are
    excluded from the computed centroid; `sample_count` reflects only the
    clips actually used. `min_sample_similarity`/`min_samples` normally come
    from the caller's loaded `AppSettings.remove_outliers`. `on_progress`, if
    given, is called as `(clips_embedded, total_unique_clips)` after each
    unique clip's embedding completes -- real step counts for a determinate
    progress display, not just a busy indicator.
    """
    player = get_player(session, player_id)
    centroid, used_count, _unused_paths = _compute_recompute_result(player_folder, embed, on_progress, min_sample_similarity, min_samples)
    _apply_centroid(player, centroid, used_count)
    session.add(player)
    session.flush()
    return player


def cleanup_voice_clips(
    session: Session,
    player_id: uuid.UUID,
    player_folder: Path,
    embed: Callable[[Path], Embedding],
    on_progress: Callable[[int, int], None] | None = None,
    min_sample_similarity: float = DEFAULT_MIN_SAMPLE_SIMILARITY,
    min_samples: int = DEFAULT_MIN_SAMPLES,
) -> tuple[Player, list[str]]:
    """Recompute the centroid, then delete every clip file that didn't contribute to it.

    Unlike a plain recompute, this permanently removes duplicate and outlier
    clip files from disk rather than just excluding them from the centroid --
    it owns its own recompute-while-pruning pass instead of leaving the
    unused files to be re-discovered (and re-embedded) next time. Files are
    deleted before the player's centroid fields are written, mirroring
    `delete_voice_clip`'s disk-then-DB order, so a mid-loop deletion failure
    can't leave a persisted centroid that disagrees with what's on disk.
    `min_sample_similarity`/`min_samples` normally come from the caller's
    loaded `AppSettings.remove_outliers`. Returns the updated player and the
    filenames that were deleted.
    """
    player = get_player(session, player_id)
    centroid, used_count, unused_paths = _compute_recompute_result(player_folder, embed, on_progress, min_sample_similarity, min_samples)
    for path in unused_paths:
        path.unlink(missing_ok=True)
    _apply_centroid(player, centroid, used_count)
    session.add(player)
    session.flush()
    return player, [path.name for path in unused_paths]


def delete_voice_clip(
    session: Session,
    player_id: uuid.UUID,
    filename: str,
    player_folder: Path,
    embed: Callable[[Path], Embedding],
    on_progress: Callable[[int, int], None] | None = None,
    min_sample_similarity: float = DEFAULT_MIN_SAMPLE_SIMILARITY,
    min_samples: int = DEFAULT_MIN_SAMPLES,
) -> Player:
    """Delete a voice clip file, then auto-recompute the centroid over what remains."""
    clip_path = player_folder / filename
    if not clip_path.is_file():
        raise ValueError(f"Voice clip '{filename}' not found.")
    clip_path.unlink()
    return recompute_centroid(session, player_id, player_folder, embed, on_progress, min_sample_similarity, min_samples)
