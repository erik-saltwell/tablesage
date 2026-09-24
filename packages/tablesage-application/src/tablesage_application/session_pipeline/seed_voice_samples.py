"""Process Session's Seed Player Voice Samples step: turn each new player's reviewed utterances into voice clips.

For every player listed in `reviewed_new_speaker_assignments.json`, the kept utterances are cut from the
Session audio into that player's folder and their centroid is recomputed. The reviewer is the quality gate,
so the only filter is the embedding model's technical length floor. Players the reviewed file doesn't list
are never touched, so re-running after seeding (when nobody is new any more) changes nothing.

`seeded_voice_samples.json` is the step's receipt and completion marker: the real output lives in player
folders and the database, which the artifact graph can't see.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import widelog
from pydantic import BaseModel
from sqlmodel import Session
from tablesage_tools.audio import extract_clip
from tablesage_tools.embeddings import Embedding
from tablesage_tools.model import Transcript

from ..paths import ARTIFACTS, ArtifactName
from ..players_from_session import generated_session_filename
from ..voice_clips import clips
from .atomic_files import atomic_write

OnProgress = Callable[[str, int, int], None]


class SeededPlayer(BaseModel, frozen=True):
    player_id: uuid.UUID
    player_name: str
    clip_filenames: tuple[str, ...]
    # Clips that contributed to the recomputed centroid (duplicates and outliers excluded); 0 leaves the player new.
    sample_count: int


class SeededVoiceSamples(BaseModel, frozen=True):
    """`seeded_voice_samples.json`: what the step wrote for each player in the reviewed assignments."""

    players: tuple[SeededPlayer, ...]

    @classmethod
    def load(cls, path: Path) -> SeededVoiceSamples:
        return cls.model_validate_json(path.read_bytes())


@dataclass(frozen=True)
class SeedTarget:
    """One reviewed player: where their clips go and which name-corrected utterances become clips."""

    player_id: uuid.UUID
    player_name: str
    folder: Path
    utterance_indices: tuple[int, ...]


def receipt_path(session_folder: Path) -> Path:
    return session_folder / ARTIFACTS[ArtifactName.SEEDED_VOICE_SAMPLES].filename


def seed_voice_samples(
    session: Session,
    session_id: uuid.UUID,
    session_folder: Path,
    campaign_name: str,
    session_name: str,
    targets: Sequence[SeedTarget],
    embed: Callable[[Path], Embedding],
    min_embeddable_clip_seconds: float,
    min_sample_similarity: float,
    min_samples: int,
    on_progress: OnProgress | None = None,
) -> SeededVoiceSamples:
    """Replace each target's clips from this Session with their kept utterances, then recompute their centroids.

    Extract-then-delete-old per player, as in "From Session", so a failure partway never leaves a player
    worse off. Centroid changes are flushed, not committed: the caller commits, then writes the receipt.
    """
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename)
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
    session_hash = clips.hash8(str(session_id))
    selected = {
        target.player_id: [
            transcript.utterances[index]
            for index in target.utterance_indices
            if transcript.utterances[index].end - transcript.utterances[index].start >= min_embeddable_clip_seconds
        ]
        for target in targets
    }
    total = sum(len(utterances) for utterances in selected.values())

    with widelog.wide_event(op="seed_voice_samples", session_id=str(session_id), player_count=len(targets), clip_count=total) as log:

        async def extract_all() -> dict[uuid.UUID, tuple[str, ...]]:
            written: dict[uuid.UUID, tuple[str, ...]] = {}
            completed = 0
            for target in targets:
                target.folder.mkdir(parents=True, exist_ok=True)
                prior = clips.find_clips_by_hash_segment(target.folder, "session", session_hash)
                names: list[str] = []
                for utterance in selected[target.player_id]:
                    filename = generated_session_filename(target.player_name, campaign_name, session_name, session_hash)
                    await extract_clip(audio_path, target.folder / filename, utterance.start, utterance.end)
                    names.append(filename)
                    completed += 1
                    if on_progress is not None:
                        on_progress("Cutting voice clips…", completed, total)
                for old_clip in prior:
                    old_clip.unlink(missing_ok=True)
                written[target.player_id] = tuple(names)
            return written

        # Nothing to cut when no players are listed; Process Session completes that (skipped) case on its UI
        # thread, where an event loop is already running.
        written = asyncio.run(extract_all()) if targets else {}

        seeded: list[SeededPlayer] = []
        for index, target in enumerate(targets, start=1):
            if on_progress is not None:
                on_progress("Recomputing voice profiles…", index - 1, len(targets))
            player = clips.recompute_centroid(session, target.player_id, target.folder, embed, None, min_sample_similarity, min_samples)
            seeded.append(
                SeededPlayer(
                    player_id=target.player_id,
                    player_name=target.player_name,
                    clip_filenames=written[target.player_id],
                    sample_count=player.sample_count,
                )
            )
        log.set(sample_counts={player.player_name: player.sample_count for player in seeded})
        return SeededVoiceSamples(players=tuple(seeded))


def save_receipt(session_folder: Path, receipt: SeededVoiceSamples) -> None:
    atomic_write(receipt_path(session_folder), receipt.model_dump_json(indent=2).encode("utf-8"))
