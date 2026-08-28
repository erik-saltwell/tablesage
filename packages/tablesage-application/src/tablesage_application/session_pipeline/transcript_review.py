from __future__ import annotations

import asyncio
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import widelog
from tablesage_tools.audio.ffmpeg import extract_clip
from tablesage_tools.model import Transcript
from tablesage_tools.speakers import MIN_UTTERANCE_DURATION_SECONDS

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

    An utterance whose `end` isn't strictly after its `start` (ffmpeg's `-to` is an absolute
    timestamp, not a duration, so `-ss X -to X` aborts with "-to value smaller than -ss") has no
    clip extracted -- this really happens: a handful of utterances per real session come back
    from the transcription provider with an identical start/end on their one word (seen, e.g., a
    zero-duration "Yeah."). `identify_speakers` already routes around this at transcribe time via
    its own too-short-to-embed floor, so it only surfaces here, where every utterance (not just
    embeddable ones) needs a clip. `SpeakerReviewScreen` skips playback for a row with no clip
    file rather than erroring -- there's nothing to play, but the utterance is still reviewable
    and assignable from its text.
    """
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
    clip_dir = review_clips_folder(session_folder)
    clip_dir.mkdir(parents=True, exist_ok=True)

    total = len(transcript.utterances)
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename

    async def _extract_all() -> int:
        skipped = 0
        for index, utterance in enumerate(transcript.utterances):
            if utterance.end <= utterance.start:
                skipped += 1
            else:
                await extract_clip(audio_path, clip_path(session_folder, index), utterance.start, utterance.end)
            if on_progress is not None:
                on_progress(index + 1, total)
        return skipped

    with widelog.wide_event(op="extract_review_clips", session_folder=str(session_folder), utterance_count=total) as log:
        skipped_count = asyncio.run(_extract_all())
        log.set(skipped_zero_duration_count=skipped_count)

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


@dataclass(frozen=True)
class BenchmarkTranscriptResult:
    """The outcome of `generate_benchmark_transcript`, for the caller to report to the user."""

    kept_count: int
    excluded_count: int


def generate_benchmark_transcript(session_folder: Path) -> BenchmarkTranscriptResult:
    """Write `transcript_benchmark.json` -- a copy of `transcript.json` with every utterance under
    `MIN_UTTERANCE_DURATION_SECONDS` dropped.

    Scoring `identify_speakers`' output against hand-corrected ground truth that still includes
    those utterances is misleading: `identify_speakers` never attempts a judgment on one (see
    `MIN_UTTERANCE_DURATION_SECONDS`'s docstring) and always leaves it `UNASSIGNED_SPEAKER`
    regardless of what a human later assigned it from context alone -- scoring that as a miss
    measures the too-short guard, not speaker-identification accuracy.

    This is a derived, disposable, on-demand artifact, not a second source of truth: it is never
    read by any other pipeline step, never hand-edited, and always regenerated wholesale from
    whatever `transcript.json` currently contains -- the canonical transcript (including the
    short utterances) stays exactly what `T` writes and what Speaker Review reviews. A benchmark
    script should always regenerate this immediately before scoring rather than trusting an old
    copy, since nothing keeps it in sync with `transcript.json` automatically.
    """
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
    kept = [utterance for utterance in transcript.utterances if utterance.end - utterance.start >= MIN_UTTERANCE_DURATION_SECONDS]
    excluded_count = len(transcript.utterances) - len(kept)

    with widelog.wide_event(
        op="generate_benchmark_transcript",
        session_folder=str(session_folder),
        kept_count=len(kept),
        excluded_count=excluded_count,
    ):
        Transcript(utterances=kept).save(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_BENCHMARK].filename)

    return BenchmarkTranscriptResult(kept_count=len(kept), excluded_count=excluded_count)


def count_adjusted_utterances(session_folder: Path) -> int:
    """How many utterances a human has hand-corrected -- drives the re-transcribe confirmation's wording.

    Called unconditionally by the `T` guard, including a session's very first transcribe attempt
    (before `transcript.json` exists at all) -- no file trivially means nothing has been
    hand-corrected yet, not an error.
    """
    transcript_path = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename
    if not transcript_path.is_file():
        return 0
    transcript = Transcript.load(transcript_path)
    return sum(1 for utterance in transcript.utterances if utterance.adjusted)
