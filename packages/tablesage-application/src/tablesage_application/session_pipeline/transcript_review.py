from __future__ import annotations

import asyncio
import shutil
from collections.abc import Callable
from pathlib import Path

from tablesage_tools.audio.ffmpeg import extract_clip
from tablesage_tools.model import Transcript

from ..paths import ARTIFACTS, ArtifactName

REVIEW_CLIPS_DIRNAME = "speaker_review_clips"


def review_clips_folder(session_folder: Path) -> Path:
    return session_folder / REVIEW_CLIPS_DIRNAME


def _clip_filename(utterance_index: int) -> str:
    return f"{utterance_index:04d}.wav"


def clip_path(session_folder: Path, utterance_index: int) -> Path:
    return review_clips_folder(session_folder) / _clip_filename(utterance_index)


def extract_review_clips(session_folder: Path, on_progress: Callable[[int, int], None] | None = None) -> tuple[Transcript, Path]:
    """Load `transcript.json` and pre-extract every utterance's audio into `speaker_review_clips/`.

    Runs entirely up front (behind a progress dialog, per the caller) so Speaker Review's
    table -- linear playback or a mouse click straight to an arbitrary row -- never waits
    on ffmpeg mid-session. Re-extracting is idempotent: existing clips are overwritten.
    """
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
    clip_dir = review_clips_folder(session_folder)
    clip_dir.mkdir(parents=True, exist_ok=True)

    total = len(transcript.utterances)
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename

    async def _extract_all() -> None:
        for index, utterance in enumerate(transcript.utterances):
            await extract_clip(audio_path, clip_path(session_folder, index), utterance.start, utterance.end)
            if on_progress is not None:
                on_progress(index + 1, total)

    asyncio.run(_extract_all())
    return transcript, clip_dir


def discard_review_clips(session_folder: Path) -> None:
    """Delete the review clip cache -- called when Speaker Review closes. Never persists across screen opens."""
    shutil.rmtree(review_clips_folder(session_folder), ignore_errors=True)


def assign_speaker(transcript: Transcript, utterance_index: int, speaker: str) -> Transcript:
    """Return a copy of `transcript` with `utterances[utterance_index]`'s speaker set to `speaker`.

    `adjusted` becomes True only if `speaker` differs from the utterance's current value --
    confirming an already-correct label (or leaving it untouched) never sets it -- and, once
    True, stays True even if a later edit changes the value again.
    """
    utterance = transcript.utterances[utterance_index]
    changed = speaker != utterance.speaker
    updated = utterance.model_copy(update={"speaker": speaker, "adjusted": utterance.adjusted or changed})
    new_utterances = list(transcript.utterances)
    new_utterances[utterance_index] = updated
    return Transcript(utterances=new_utterances)


def count_adjusted_utterances(session_folder: Path) -> int:
    """How many utterances a human has hand-corrected -- drives the re-transcribe confirmation's wording."""
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
    return sum(1 for utterance in transcript.utterances if utterance.adjusted)
