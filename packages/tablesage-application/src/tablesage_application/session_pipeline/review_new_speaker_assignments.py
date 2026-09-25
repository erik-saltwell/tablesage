"""Process Session's Review New Speaker Assignments step: a human keeps or removes each proposed utterance.

What survives becomes each new player's voice samples. The reviewer removes utterances and can grow a
player's list only through Find More (see `find_voice_matches`), whose additions they then review like
any other; utterances are never moved between players. The reviewed artifact has the input's shape and
stores what was kept, plus each player's removed Find More additions; other rejections are the proposed
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
from .atomic_files import atomic_write
from .isolate_new_speakers import NewSpeakerAssignments
from .speech import speech_duration

REVIEW_CLIPS_DIRNAME = "new_speaker_review_clips"


class ReviewedNewSpeakerAssignment(BaseModel, frozen=True):
    player_id: uuid.UUID
    player_name: str
    utterance_indices: tuple[int, ...]
    # Find More additions the reviewer removed: they keep counting as "not this player" on later searches.
    rejected_voice_matches: tuple[int, ...] = ()


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

    # Added on the review screen by Find More, rather than proposed by Isolate New Speakers.
    found_by_find_more: bool = False

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
    # Indices of utterances to show as removed on entry (from a current reviewed file).
    removed: frozenset[int]
    # Kept speech below which a player is flagged, and how much one Find More aims to add.
    target_speech_seconds: float = 0.0


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


def review_utterance(
    transcript: Transcript, index: int, explanations: Sequence[str] = (), *, found_by_find_more: bool = False
) -> ReviewUtterance:
    utterance = transcript.utterances[index]
    return ReviewUtterance(
        index=index,
        text=utterance.punctuated_text or utterance.text,
        speech_seconds=speech_duration(utterance),
        clip_seconds=max(0.0, utterance.end - utterance.start),
        explanations=tuple(dict.fromkeys(explanations)),
        found_by_find_more=found_by_find_more,
    )


def review_data(
    session_folder: Path,
    proposals: NewSpeakerAssignments,
    saved: ReviewedNewSpeakerAssignments | None,
    target_speech_seconds: float = 0.0,
) -> ReviewData:
    """Everything the review screen shows. `saved` is the reviewed file only when it is current; its Find More
    additions, kept or rejected, follow the proposed utterances."""
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename)
    saved_players = {player.player_id: player for player in saved.players} if saved is not None else {}
    players: list[ReviewPlayer] = []
    removed: set[int] = set()
    for proposal in proposals.players:
        explanations: dict[int, list[str]] = {}
        for entry in proposals.evidence:
            if entry.player_id == proposal.player_id:
                for index in entry.utterance_indices:
                    explanations.setdefault(index, []).append(entry.explanation)
        proposed = set(proposal.utterance_indices)
        utterances = [review_utterance(transcript, index, explanations.get(index, ())) for index in proposal.utterance_indices]
        reviewed = saved_players.get(proposal.player_id)
        if reviewed is not None:
            kept = set(reviewed.utterance_indices)
            rejected = set(reviewed.rejected_voice_matches) - kept - proposed
            additions = sorted((kept - proposed) | rejected)
            utterances.extend(review_utterance(transcript, index, found_by_find_more=True) for index in additions)
            removed.update((proposed - kept) | rejected)
        players.append(ReviewPlayer(player_id=proposal.player_id, player_name=proposal.player_name, utterances=tuple(utterances)))
    return ReviewData(players=tuple(players), removed=frozenset(removed), target_speech_seconds=target_speech_seconds)


def save_review(
    session_folder: Path,
    proposals: NewSpeakerAssignments,
    kept: Mapping[uuid.UUID, Sequence[int]],
    current: ReviewedNewSpeakerAssignments | None,
    rejected: Mapping[uuid.UUID, Sequence[int]] | None = None,
) -> bool:
    """Write the reviewed file unless `current` (the saved file, only when it is current) keeps the same utterances.

    Staleness is modification-time based, so rewriting an unchanged review would needlessly
    invalidate every downstream artifact. For the same reason a change to `rejected` (each player's
    removed Find More additions) alone isn't saved. Proposed indices keep their order; Find More
    additions follow in transcript order. Returns whether it wrote.
    """
    players: list[ReviewedNewSpeakerAssignment] = []
    for proposal in proposals.players:
        player_kept = set(kept.get(proposal.player_id, ()))
        proposed = [i for i in proposal.utterance_indices if i in player_kept]
        players.append(
            ReviewedNewSpeakerAssignment(
                player_id=proposal.player_id,
                player_name=proposal.player_name,
                utterance_indices=(*proposed, *sorted(player_kept - set(proposed))),
                rejected_voice_matches=tuple(sorted(set((rejected or {}).get(proposal.player_id, ())) - player_kept)),
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
    """Extract a playback clip for each listed utterance, replacing any left from an earlier visit.

    An utterance whose `end` isn't after its `start` gets no clip (ffmpeg rejects it); the
    screen treats a missing clip as silent.
    """
    discard_clips(session_folder)
    clips_folder(session_folder).mkdir(parents=True)
    extract_more_clips(session_folder, indices, on_progress)


def extract_more_clips(session_folder: Path, indices: Sequence[int], on_progress: Callable[[int, int], None] | None = None) -> None:
    """Extract playback clips for `indices` (such as Find More's additions), leaving existing clips alone."""
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename)
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
    clips_folder(session_folder).mkdir(parents=True, exist_ok=True)

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
