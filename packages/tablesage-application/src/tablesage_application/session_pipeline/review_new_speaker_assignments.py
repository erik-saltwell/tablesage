"""Process Session's Review New Speaker Assignments step: a human keeps or removes each proposed utterance.

What survives becomes each new player's voice samples, so the review is remove-only: it can
shrink a player's list but never add to it or move utterances between players. The reviewed
artifact has the input's shape and stores only what was kept; rejections are the proposed
indices minus the kept ones.
"""

from __future__ import annotations

import asyncio
import shutil
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import widelog
from pydantic import BaseModel, ValidationError
from tablesage_tools.audio import extract_clip
from tablesage_tools.model import Transcript

from ..paths import ARTIFACTS, ArtifactName
from .bootstrap_speakers import speech_duration
from .bootstrap_workflow import atomic_write
from .isolate_new_speakers import NewSpeakerAssignments

REVIEW_CLIPS_DIRNAME = "new_speaker_review_clips"


class ReviewedNewSpeakerAssignment(BaseModel, frozen=True):
    player_id: uuid.UUID
    player_name: str
    utterance_indices: tuple[int, ...]


class ReviewedNewSpeakerAssignments(BaseModel, frozen=True):
    """`reviewed_new_speaker_assignments.json`: the kept indices into `name_corrected_transcript.json`."""

    players: tuple[ReviewedNewSpeakerAssignment, ...]

    def kept(self) -> dict[uuid.UUID, frozenset[int]]:
        return {player.player_id: frozenset(player.utterance_indices) for player in self.players}


@dataclass(frozen=True)
class ReviewUtterance:
    index: int
    text: str
    # Speech seconds (word-interval union), the same measure Isolate New Speakers thresholds on.
    speech_seconds: float
    # Clip length (end - start), which playback runs for.
    clip_seconds: float
    # The player's own evidence explanations citing this utterance; empty for a voice-fallback addition.
    explanations: tuple[str, ...]

    @property
    def added_by_voice_match(self) -> bool:
        return not self.explanations


@dataclass(frozen=True)
class ReviewPlayer:
    player_id: uuid.UUID
    player_name: str
    utterances: tuple[ReviewUtterance, ...]


@dataclass(frozen=True)
class ReviewData:
    players: tuple[ReviewPlayer, ...]
    # Indices of proposed utterances to show as removed on entry (from a current reviewed file).
    removed: frozenset[int]
    min_total_speech_seconds: float


def reviewed_path(session_folder: Path) -> Path:
    return session_folder / ARTIFACTS[ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS].filename


def load_reviewed(session_folder: Path) -> ReviewedNewSpeakerAssignments | None:
    """The saved review, or None when it is missing or unreadable."""
    try:
        return ReviewedNewSpeakerAssignments.model_validate_json(reviewed_path(session_folder).read_bytes())
    except (OSError, ValidationError):
        return None


def load_proposals(session_folder: Path) -> NewSpeakerAssignments:
    return NewSpeakerAssignments.load(session_folder / ARTIFACTS[ArtifactName.NEW_SPEAKER_ASSIGNMENTS].filename)


def review_data(
    session_folder: Path, proposals: NewSpeakerAssignments, saved: ReviewedNewSpeakerAssignments | None, min_total_speech_seconds: float
) -> ReviewData:
    """Everything the review screen shows. `saved` is the reviewed file only when it is current."""
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename)
    players: list[ReviewPlayer] = []
    for proposal in proposals.players:
        explanations: dict[int, list[str]] = {}
        for entry in proposals.evidence:
            if entry.player_id == proposal.player_id:
                for index in entry.utterance_indices:
                    explanations.setdefault(index, []).append(entry.explanation)
        players.append(
            ReviewPlayer(
                player_id=proposal.player_id,
                player_name=proposal.player_name,
                utterances=tuple(
                    ReviewUtterance(
                        index=index,
                        text=transcript.utterances[index].punctuated_text or transcript.utterances[index].text,
                        speech_seconds=speech_duration(transcript.utterances[index]),
                        clip_seconds=max(0.0, transcript.utterances[index].end - transcript.utterances[index].start),
                        explanations=tuple(dict.fromkeys(explanations.get(index, ()))),
                    )
                    for index in proposal.utterance_indices
                ),
            )
        )
    removed: set[int] = set()
    if saved is not None:
        kept = saved.kept()
        for proposal in proposals.players:
            removed.update(set(proposal.utterance_indices) - kept.get(proposal.player_id, frozenset()))
    return ReviewData(players=tuple(players), removed=frozenset(removed), min_total_speech_seconds=min_total_speech_seconds)


def save_review(
    session_folder: Path,
    proposals: NewSpeakerAssignments,
    kept: Mapping[uuid.UUID, Sequence[int]],
    current: ReviewedNewSpeakerAssignments | None,
) -> bool:
    """Write the reviewed file unless `current` (the saved file, only when it is current) already matches.

    Staleness is modification-time based, so rewriting an unchanged review would needlessly
    invalidate every downstream artifact. Only proposed indices can be kept. Returns whether it wrote.
    """
    players: list[ReviewedNewSpeakerAssignment] = []
    for proposal in proposals.players:
        player_kept = set(kept.get(proposal.player_id, ()))
        players.append(
            ReviewedNewSpeakerAssignment(
                player_id=proposal.player_id,
                player_name=proposal.player_name,
                utterance_indices=tuple(i for i in proposal.utterance_indices if i in player_kept),
            )
        )
    reviewed = ReviewedNewSpeakerAssignments(players=tuple(players))
    if current is not None and current.kept() == reviewed.kept():
        return False
    atomic_write(reviewed_path(session_folder), reviewed.model_dump_json(indent=2).encode("utf-8") + b"\n")
    return True


# Playback clips -- extracted when the screen opens and removed when it closes.


def clips_folder(session_folder: Path) -> Path:
    return session_folder / REVIEW_CLIPS_DIRNAME


def clip_path(session_folder: Path, utterance_index: int) -> Path:
    return clips_folder(session_folder) / f"{utterance_index:04d}.wav"


def extract_clips(session_folder: Path, indices: Sequence[int], on_progress: Callable[[int, int], None] | None = None) -> None:
    """Extract a playback clip for each proposed utterance, replacing any left from an earlier visit.

    An utterance whose `end` isn't after its `start` gets no clip (ffmpeg rejects it); the
    screen treats a missing clip as silent.
    """
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename)
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
    discard_clips(session_folder)
    clips_folder(session_folder).mkdir(parents=True)

    async def extract_all() -> int:
        skipped = 0
        for done, index in enumerate(indices, start=1):
            utterance = transcript.utterances[index]
            if utterance.end <= utterance.start:
                skipped += 1
            else:
                await extract_clip(audio_path, clip_path(session_folder, index), utterance.start, utterance.end)
            if on_progress is not None:
                on_progress(done, len(indices))
        return skipped

    with widelog.wide_event(op="extract_new_speaker_review_clips", session_folder=str(session_folder), clip_count=len(indices)) as log:
        log.set(skipped_zero_duration_count=asyncio.run(extract_all()))


def discard_clips(session_folder: Path) -> None:
    shutil.rmtree(clips_folder(session_folder), ignore_errors=True)
