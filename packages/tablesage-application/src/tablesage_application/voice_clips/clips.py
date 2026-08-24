from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
import tempfile
import uuid
import wave
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import widelog
from sqlmodel import Session
from tablesage_model.model import Player
from tablesage_tools.audio import clean_clip
from tablesage_tools.embeddings import DEFAULT_MIN_SAMPLE_SIMILARITY, DEFAULT_MIN_SAMPLES, Embedding, compute_centroid

from ..entities.players import get_player
from ..paths import VOICE_CLIP_GLOB

# `import-<player_slug>-<sourcehash8>-<uuid4hex>.wav` -- see
# `.documentation/import_player_from_filesystem.md`. The hash segment is the
# only part matching relies on (see `find_clips_by_hash_segment`); the slug
# is a cosmetic, as-of-import-time snapshot that goes stale (harmlessly) if
# the player is later renamed.


@dataclass(frozen=True)
class VoiceClip:
    """A voice clip file on disk. Has no database row of its own."""

    filename: str
    duration_seconds: float


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
    with widelog.wide_event(op="recompute_centroid", player_id=str(player_id), player_folder=str(player_folder)) as log:
        player = get_player(session, player_id)
        centroid, used_count, _unused_paths = _compute_recompute_result(
            player_folder, embed, on_progress, min_sample_similarity, min_samples
        )
        _apply_centroid(player, centroid, used_count)
        session.add(player)
        session.flush()
        log.set(used_count=used_count)
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
    with widelog.wide_event(op="cleanup_voice_clips", player_id=str(player_id), player_folder=str(player_folder)) as log:
        player = get_player(session, player_id)
        centroid, used_count, unused_paths = _compute_recompute_result(
            player_folder, embed, on_progress, min_sample_similarity, min_samples
        )
        for path in unused_paths:
            path.unlink(missing_ok=True)
        _apply_centroid(player, centroid, used_count)
        session.add(player)
        session.flush()
        log.set(used_count=used_count, deleted_count=len(unused_paths))
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
    with widelog.wide_event(op="delete_voice_clip", player_id=str(player_id), filename=filename, player_folder=str(player_folder)):
        clip_path = player_folder / filename
        if not clip_path.is_file():
            raise ValueError(f"Voice clip '{filename}' not found.")
        clip_path.unlink()
        return recompute_centroid(session, player_id, player_folder, embed, on_progress, min_sample_similarity, min_samples)


@dataclass(frozen=True)
class ImportResult:
    """The outcome of a directory import, for the caller to report to the user."""

    imported_count: int
    replaced_count: int
    rejected_filenames: tuple[str, ...]
    removed_outlier_filenames: tuple[str, ...] = field(default=())


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return slug or "clip"


def hash8(value: str) -> str:
    """An 8-hex-char stable hash, used as the matching segment in a generated clip filename."""
    return hashlib.sha256(value.encode()).hexdigest()[:8]


def _source_hash(source_dir: Path) -> str:
    return hash8(str(source_dir.resolve()))


def _generated_import_filename(player_name: str, source_hash: str) -> str:
    return f"import-{slugify(player_name)}-{source_hash}-{uuid.uuid4().hex}.wav"


def find_clips_by_hash_segment(player_folder: Path, prefix: str, hash_value: str) -> list[Path]:
    """Find clips in `player_folder` matching `<prefix>-...-<hash_value>-<uuid4hex>.wav`.

    Matching is by the hash segment only -- stable across player/campaign/session renames,
    unlike matching on the cosmetic slug segments would be. Shared by directory import
    (`prefix="import"`, hashing the source directory), "enhance from session"
    (`prefix="session"`, hashing the session id), and "import players from audio file"
    (`prefix="diarized"`, hashing the picked audio file's resolved path).
    """
    if not player_folder.exists():
        return []
    pattern = re.compile(rf"^{re.escape(prefix)}-.+-([0-9a-f]{{8}})-[0-9a-f]{{32}}\.wav$")
    matches = []
    for path in sorted(player_folder.glob(f"{prefix}-*.wav")):
        match = pattern.match(path.name)
        if match and match.group(1) == hash_value:
            matches.append(path)
    return matches


def validate_import_source(source_dir: Path) -> None:
    """Raise if `source_dir` isn't a directory containing at least one `.wav` file (non-recursive)."""
    if not source_dir.is_dir():
        raise ValueError(f"'{source_dir}' is not a directory.")
    if next(source_dir.glob(VOICE_CLIP_GLOB), None) is None:
        raise ValueError(f"'{source_dir}' contains no .wav files.")


def find_prior_import_clips(player_folder: Path, source_dir: Path) -> list[Path]:
    """Find clips in `player_folder` from a previous import of this same `source_dir`."""
    return find_clips_by_hash_segment(player_folder, "import", _source_hash(source_dir))


def import_voice_clips(
    session: Session,
    player_id: uuid.UUID,
    player_name: str,
    source_dir: Path,
    player_folder: Path,
    embed: Callable[[Path], Embedding],
    on_progress: Callable[[int, int], None] | None = None,
    min_sample_similarity: float = DEFAULT_MIN_SAMPLE_SIMILARITY,
    min_samples: int = DEFAULT_MIN_SAMPLES,
    *,
    should_clean_audio: bool = False,
    normalize_volume: bool = False,
) -> tuple[Player, ImportResult]:
    """Import every `.wav` file in `source_dir` as a new voice clip, then auto-recompute the centroid.

    Copy-then-delete, not delete-then-copy: a re-import of the same source
    directory replaces its prior clips as a unit (see
    `find_prior_import_clips`), but the old clips are only deleted after the
    new ones are safely copied and embedded, so a bad import leaves the
    player's previous samples intact rather than gone. Each source file is
    copied and embedded independently -- a file that fails to embed is
    skipped and reported rather than aborting the whole import, matching how
    `compute_centroid` already treats duplicates/outliers as "exclude, don't
    fail." `min_sample_similarity`/`min_samples` normally come from the
    caller's loaded `AppSettings.remove_outliers`.

    When `should_clean_audio` is set, each source file is first run through
    `clean_clip` (Mossformer2 denoise, optionally loudness-normalized per
    `normalize_volume`) into a scratch temp directory, and the cleaned result
    is what gets copied into `player_folder` -- so a rejected/outlier clip is
    always judged on its cleaned audio, matching what actually lands on disk.
    Cleaning also opts the import into deleting embedding outliers from disk
    (not just excluding them from the centroid), mirroring `cleanup_voice_clips`,
    since a clean pass is the moment the user has already signaled they want
    higher-quality samples.
    """
    with widelog.wide_event(
        op="import_voice_clips",
        player_id=str(player_id),
        player_name=player_name,
        source_dir=str(source_dir),
        should_clean_audio=should_clean_audio,
    ) as log:
        validate_import_source(source_dir)
        source_files = sorted(source_dir.glob(VOICE_CLIP_GLOB))
        prior_clips = find_prior_import_clips(player_folder, source_dir)
        source_hash = _source_hash(source_dir)

        player_folder.mkdir(parents=True, exist_ok=True)
        rejected: list[str] = []
        imported_count = 0
        total = len(source_files)

        clean_dir = Path(tempfile.mkdtemp(prefix="tablesage-clean-")) if should_clean_audio else None
        try:
            for index, source_file in enumerate(source_files, start=1):
                target = player_folder / _generated_import_filename(player_name, source_hash)
                if clean_dir is not None:
                    cleaned_file = clean_dir / source_file.name
                    asyncio.run(clean_clip(source_file, cleaned_file, normalize=normalize_volume))
                    shutil.copyfile(cleaned_file, target)
                    cleaned_file.unlink(missing_ok=True)
                else:
                    shutil.copyfile(source_file, target)
                try:
                    embed(target)
                except Exception:
                    target.unlink(missing_ok=True)
                    rejected.append(source_file.name)
                else:
                    imported_count += 1
                if on_progress is not None:
                    on_progress(index, total)
        finally:
            if clean_dir is not None:
                shutil.rmtree(clean_dir, ignore_errors=True)

        for old_clip in prior_clips:
            old_clip.unlink(missing_ok=True)

        player = get_player(session, player_id)
        centroid, used_count, unused_paths = _compute_recompute_result(player_folder, embed, None, min_sample_similarity, min_samples)
        removed_outliers: tuple[str, ...] = ()
        if should_clean_audio and unused_paths:
            for path in unused_paths:
                path.unlink(missing_ok=True)
            removed_outliers = tuple(path.name for path in unused_paths)
        _apply_centroid(player, centroid, used_count)
        session.add(player)
        session.flush()

        result = ImportResult(
            imported_count=imported_count,
            replaced_count=len(prior_clips),
            rejected_filenames=tuple(rejected),
            removed_outlier_filenames=removed_outliers,
        )
        log.set(
            imported_count=imported_count,
            replaced_count=len(prior_clips),
            rejected_count=len(rejected),
            removed_outlier_count=len(removed_outliers),
        )
        return player, result
