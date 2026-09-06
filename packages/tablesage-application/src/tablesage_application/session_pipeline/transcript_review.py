from __future__ import annotations

import asyncio
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import widelog
from tablesage_tools.audio.ffmpeg import extract_clip
from tablesage_tools.model import Transcript
from tablesage_tools.speakers import MIN_UTTERANCE_DURATION_SECONDS

from ..paths import ARTIFACTS, ArtifactName
from .artifacts import delete_artifact

REVIEW_CLIPS_DIRNAME = "speaker_review_clips"


def review_clips_folder(session_folder: Path) -> Path:
    return session_folder / REVIEW_CLIPS_DIRNAME


def _clip_filename(utterance_index: int) -> str:
    return f"{utterance_index:04d}.wav"


def clip_path(session_folder: Path, utterance_index: int) -> Path:
    return review_clips_folder(session_folder) / _clip_filename(utterance_index)


def _artifact_path(session_folder: Path, name: ArtifactName) -> Path:
    return session_folder / ARTIFACTS[name].filename


def load_review_transcript(session_folder: Path) -> Transcript:
    """Load the last completed review when present, otherwise the machine transcript."""
    reviewed_path = _artifact_path(session_folder, ArtifactName.REVIEWED_TRANSCRIPT)
    source = reviewed_path if reviewed_path.is_file() else _artifact_path(session_folder, ArtifactName.TRANSCRIPT)
    return Transcript.load(source)


def extract_review_clips(session_folder: Path, on_progress: Callable[[int, int], None] | None = None) -> tuple[Transcript, Path]:
    """Load the review source and pre-extract every utterance's audio into `speaker_review_clips/`.

    Runs entirely up front (behind a progress dialog, per the caller) so Manual Review's
    table -- linear playback or a mouse click straight to an arbitrary row -- never waits
    on ffmpeg mid-session. Re-extracting is idempotent: existing clips are overwritten.

    An utterance whose `end` isn't strictly after its `start` (ffmpeg's `-to` is an absolute
    timestamp, not a duration, so `-ss X -to X` aborts with "-to value smaller than -ss") has no
    clip extracted -- this really happens: a handful of utterances per real session come back
    from the transcription provider with an identical start/end on their one word (seen, e.g., a
    zero-duration "Yeah."). `identify_speakers` already routes around this at transcribe time via
    its own too-short-to-embed floor, so it only surfaces here, where every utterance (not just
    embeddable ones) needs a clip. `ManualReviewScreen` skips playback for a row with no clip
    file rather than erroring -- there's nothing to play, but the utterance is still reviewable
    and assignable from its text.
    """
    transcript = load_review_transcript(session_folder)
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
    """Delete the review clip cache -- called when Manual Review closes. Never persists across screen opens."""
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


def edit_utterance(transcript: Transcript, utterance_index: int, speaker: str, text: str) -> Transcript:
    """Return a copy with an utterance's speaker and displayed text edited together.

    Like the number-key speaker assignment, an actual change marks the utterance adjusted and
    that marker remains sticky across later edits. The caller validates that `text` is nonblank.
    """
    utterance = transcript.utterances[utterance_index]
    current_text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
    changed = speaker != utterance.speaker or text != current_text
    updated = utterance.model_copy(
        update={
            "speaker": speaker,
            "punctuated_text": text,
            "adjusted": utterance.adjusted or changed,
        }
    )
    new_utterances = list(transcript.utterances)
    new_utterances[utterance_index] = updated
    return Transcript(utterances=new_utterances)


def delete_utterance(transcript: Transcript, utterance_index: int) -> Transcript:
    """Return a copy of `transcript` with `utterances[utterance_index]` removed entirely.

    Unlike `assign_speaker`/`edit_utterance`, this drops the utterance from the transcript rather
    than relabeling it -- for a genuine mis-segmentation (a stray noise blip transcribed as a
    word, a duplicate split) rather than a wrong speaker or wrong text.
    """
    new_utterances = list(transcript.utterances)
    del new_utterances[utterance_index]
    return Transcript(utterances=new_utterances)


@dataclass(frozen=True)
class ReplaceTextResult:
    """The outcome of `replace_text`, for the caller to report to the user."""

    utterance_count: int
    occurrence_count: int


def count_occurrences(transcript: Transcript, find: str, case_sensitive: bool) -> int:
    """How many times `find` occurs across every utterance's displayed text.

    Same literal (escaped), `punctuated_text`-preferring matching as `replace_text` -- shared so a
    suggestion's displayed occurrence count and what `replace_text` will actually replace never
    disagree. An empty `find` matches nothing.
    """
    if not find:
        return 0
    pattern = re.compile(re.escape(find), 0 if case_sensitive else re.IGNORECASE)
    return sum(
        len(pattern.findall(utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text))
        for utterance in transcript.utterances
    )


def replace_text(transcript: Transcript, find: str, replacement: str, case_sensitive: bool) -> tuple[Transcript, ReplaceTextResult]:
    """Return a copy of `transcript` with every occurrence of `find` in each utterance's displayed
    text replaced by `replacement`, across the whole transcript.

    Matching is literal, not a regex -- `find` is escaped before use. `case_sensitive` controls
    only how a match is found; `replacement` is always inserted exactly as given, regardless of
    what case the matched text had. An utterance with no match is left completely untouched
    (including its `adjusted` flag); one with at least one match gets its displayed text updated
    and `adjusted` set, sticky like every other edit here. An empty `find` matches nothing.
    """
    if not find:
        return transcript, ReplaceTextResult(utterance_count=0, occurrence_count=0)

    pattern = re.compile(re.escape(find), 0 if case_sensitive else re.IGNORECASE)
    new_utterances = list(transcript.utterances)
    utterance_count = 0
    occurrence_count = 0
    for index, utterance in enumerate(transcript.utterances):
        current_text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
        new_text, count = pattern.subn(lambda _match: replacement, current_text)
        if not count:
            continue
        utterance_count += 1
        occurrence_count += count
        new_utterances[index] = utterance.model_copy(update={"punctuated_text": new_text, "adjusted": True})

    return Transcript(utterances=new_utterances), ReplaceTextResult(utterance_count=utterance_count, occurrence_count=occurrence_count)


def save_reviewed_transcript(session_folder: Path, transcript: Transcript) -> None:
    """Atomically replace the completed review, then discard artifacts derived from its source."""
    target = _artifact_path(session_folder, ArtifactName.REVIEWED_TRANSCRIPT)
    temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
    try:
        transcript.save(temporary)
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    for name in (
        ArtifactName.TRANSCRIPT_ROLES_TEXT,
        ArtifactName.TRANSCRIPT_BENCHMARK,
        ArtifactName.ROLE_TRANSCRIPT,
        ArtifactName.TRANSCRIPT_SECTIONS,
        ArtifactName.LEDGER,
        ArtifactName.PLAYER_INTRODUCTIONS,
        ArtifactName.RECAP_SUMMARY,
        ArtifactName.SUMMARY,
    ):
        delete_artifact(session_folder, name)


@dataclass(frozen=True)
class BenchmarkTranscriptResult:
    """The outcome of `generate_benchmark_transcript`, for the caller to report to the user."""

    kept_count: int
    excluded_count: int


def generate_benchmark_transcript(session_folder: Path) -> BenchmarkTranscriptResult:
    """Write `transcript_benchmark.json` from the completed review (or machine transcript) with every utterance under
    `MIN_UTTERANCE_DURATION_SECONDS` dropped.

    Scoring `identify_speakers`' output against hand-corrected ground truth that still includes
    those utterances is misleading: `identify_speakers` never attempts a judgment on one (see
    `MIN_UTTERANCE_DURATION_SECONDS`'s docstring) and always leaves it `UNASSIGNED_SPEAKER`
    regardless of what a human later assigned it from context alone -- scoring that as a miss
    measures the too-short guard, not speaker-identification accuracy.

    This is a derived, disposable, on-demand artifact, not a second source of truth: it is never
    read by any other pipeline step, never hand-edited, and always regenerated wholesale from
    the completed review when it exists, otherwise from `transcript.json`. The canonical
    transcript (including the short utterances) stays exactly what `T` writes. A benchmark
    script should always regenerate this immediately before scoring rather than trusting an old
    copy, since nothing keeps it in sync with `transcript.json` automatically.
    """
    transcript = load_review_transcript(session_folder)
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
    transcript_path = _artifact_path(session_folder, ArtifactName.REVIEWED_TRANSCRIPT)
    if not transcript_path.is_file():
        return 0
    transcript = Transcript.load(transcript_path)
    return sum(1 for utterance in transcript.utterances if utterance.adjusted)
