"""Find More, on the Review New Speaker Assignments screen: add the utterances that sound most like a player.

The player's voice is the centroid of the utterances the reviewer has kept for them. Every other unused
utterance is ranked by its lead: how much closer it is to that voice than to the nearest rival voice. The
rivals are the other attendees (stored centroids for known players, kept utterances for the other new
players) and, once the reviewer has removed any earlier Find More additions for this player, one centroid
of those rejected clips. The top of the ranking is added until the player reaches the target, or gains
another target's worth when already there. Find More always adds when anything is left, since the reviewer
listens to every addition before confirming.

Embeddings are cached per Session, so only the first search pays for embedding the whole transcript.
"""

from __future__ import annotations

import asyncio
import math
import tempfile
import time
import uuid
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import widelog
from tablesage_tools.audio import extract_clip
from tablesage_tools.embeddings import Embedding, cosine_similarity, mean_centroid
from tablesage_tools.model import Transcript

from ..paths import ARTIFACTS, ArtifactName
from .speech import speech_duration

# Concurrent ffmpeg processes while cutting clips to embed.
_EXTRACT_CONCURRENCY = 8

OnProgress = Callable[[str, int, int], None]


@dataclass
class VoiceMatchEmbeddings:
    """One Session's utterance embeddings, valid while the transcript and audio files are unchanged."""

    session_folder: Path
    stamp: tuple[int, int]
    transcript: Transcript
    by_index: dict[int, Embedding | None] = field(default_factory=dict)

    @classmethod
    def load(cls, session_folder: Path) -> VoiceMatchEmbeddings:
        return cls(session_folder, _stamp(session_folder), Transcript.load(_transcript_path(session_folder)))

    def is_current(self) -> bool:
        return self.stamp == _stamp(self.session_folder)

    def ensure(self, indices: Collection[int], embed: Callable[[Path], Embedding], message: str, on_progress: OnProgress | None) -> None:
        """Embed every index not yet cached. An utterance that can't be embedded caches as None."""
        missing = sorted(i for i in indices if i not in self.by_index)
        if not missing:
            return
        audio_path = self.session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
        with tempfile.TemporaryDirectory(dir=self.session_folder, prefix=".find-more-") as directory:
            clips: dict[int, Path] = {}
            for index in missing:
                utterance = self.transcript.utterances[index]
                if utterance.end <= utterance.start:
                    self.by_index[index] = None
                else:
                    clips[index] = Path(directory) / f"{index}.wav"
            asyncio.run(_extract_all(audio_path, self.transcript, clips))
            _report(on_progress, message, 0, len(clips))
            for done, (index, path) in enumerate(clips.items(), start=1):
                embedding = embed(path)
                self.by_index[index] = embedding if _is_finite(embedding) else None
                _report(on_progress, message, done, len(clips))

    def centroid(self, indices: Collection[int]) -> Embedding | None:
        embeddings = [e for i in indices if (e := self.by_index.get(i)) is not None]
        return mean_centroid(embeddings) if embeddings else None


@dataclass(frozen=True)
class VoiceMatchRequest:
    player_id: uuid.UUID
    # Every new player's currently kept utterances, including this player's.
    kept: Mapping[uuid.UUID, Collection[int]]
    # Every utterance already in any new player's list, kept or removed; never proposed again, so an utterance
    # belongs to at most one player (the review screen tracks removal by index alone).
    listed: Collection[int]
    # This player's removed Find More additions: together they form one rival voice.
    rejected: Collection[int]
    # Stored centroids of the attendees who already have a voice profile.
    known_voices: Sequence[Embedding]
    min_speech_seconds: float
    target_speech_seconds: float


def find_voice_matches(
    cache: VoiceMatchEmbeddings, request: VoiceMatchRequest, embed: Callable[[Path], Embedding], on_progress: OnProgress | None = None
) -> tuple[int, ...]:
    """The utterances to add to the player, best match first; empty only when nothing is left to add."""
    transcript = cache.transcript
    own = set(request.kept.get(request.player_id, ()))
    if not own:
        raise ValueError("Keep at least one utterance for this player first.")
    kept_by_others = {i for player_id, indices in request.kept.items() if player_id != request.player_id for i in indices}
    excluded = own | set(request.listed) | kept_by_others
    pool = [
        i
        for i, utterance in enumerate(transcript.utterances)
        if i not in excluded and utterance.end > utterance.start and speech_duration(utterance) >= request.min_speech_seconds
    ]
    started = time.monotonic()
    with widelog.wide_event(
        op="find_voice_matches",
        session_folder=str(cache.session_folder),
        player_id=str(request.player_id),
        kept_count=len(own),
        rejected_count=len(request.rejected),
        pool_count=len(pool),
    ) as log:
        needed = set(pool) | own | kept_by_others | set(request.rejected)
        log.set(newly_embedded_count=sum(1 for i in needed if i not in cache.by_index))
        cache.ensure(needed, embed, "Comparing voices (the first search scans the whole Session)…", on_progress)
        voice = cache.centroid(own)
        if voice is None:
            raise ValueError("None of this player's kept utterances could be embedded.")
        rivals = list(request.known_voices)
        for player_id, indices in request.kept.items():
            if player_id != request.player_id and (rival := cache.centroid(indices)) is not None:
                rivals.append(rival)
        if (rejected_voice := cache.centroid(request.rejected)) is not None:
            rivals.append(rejected_voice)

        def lead(index: int) -> float:
            embedding = cache.by_index[index]
            assert embedding is not None
            similarity = cosine_similarity(embedding, voice)
            return similarity - max((cosine_similarity(embedding, rival) for rival in rivals), default=0.0)

        leads = {i: lead(i) for i in pool if cache.by_index.get(i) is not None}
        current = sum(speech_duration(transcript.utterances[i]) for i in own)
        wanted = request.target_speech_seconds - current
        if wanted <= 0:
            wanted = request.target_speech_seconds
        added: list[int] = []
        total = 0.0
        for index in sorted(leads, key=lambda i: leads[i], reverse=True):
            if total >= wanted:
                break
            added.append(index)
            total += speech_duration(transcript.utterances[index])
        log.set(
            rival_count=len(rivals),
            candidate_count=len(leads),
            added_count=len(added),
            added_seconds=round(total, 1),
            weakest_added_lead=round(leads[added[-1]], 3) if added else None,
            elapsed_seconds=round(time.monotonic() - started, 1),
        )
    return tuple(added)


def _transcript_path(session_folder: Path) -> Path:
    return session_folder / ARTIFACTS[ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename


def _stamp(session_folder: Path) -> tuple[int, int]:
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
    return _transcript_path(session_folder).stat().st_mtime_ns, audio_path.stat().st_mtime_ns


async def _extract_all(audio_path: Path, transcript: Transcript, clips: Mapping[int, Path]) -> None:
    semaphore = asyncio.Semaphore(_EXTRACT_CONCURRENCY)

    async def extract(index: int, path: Path) -> None:
        utterance = transcript.utterances[index]
        async with semaphore:
            await extract_clip(audio_path, path, utterance.start, utterance.end)

    await asyncio.gather(*(extract(index, path) for index, path in clips.items()))


def _is_finite(embedding: Embedding) -> bool:
    return all(math.isfinite(value) for value in embedding.root) and any(value != 0 for value in embedding.root)


def _report(on_progress: OnProgress | None, message: str, completed: int, total: int) -> None:
    if on_progress is not None:
        on_progress(message, completed, total)
