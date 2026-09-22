from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import widelog
from sqlmodel import Session
from tablesage_model.settings import RemoveBackchannelsSettings, SpeakerIdentificationSettings, TranscriptionAndDiarizationSettings
from tablesage_tools.embeddings import Embedding, EmbeddingFactory
from tablesage_tools.model import Transcript, Utterance
from tablesage_tools.punctuation import punctuate_transcript
from tablesage_tools.speakers import (
    UNASSIGNED_SPEAKER,
    ClusterPropagationConfig,
    ShortUtteranceWideningConfig,
    identify_speakers,
)
from tablesage_tools.transcription import transcribe_and_diarize

from ..entities.sessions import list_attendance
from ..paths import ARTIFACTS, ArtifactName
from .artifacts import session_artifacts
from .remove_backchannels import remove_backchannels


class Stage(Enum):
    """A `transcribe_audio` pipeline stage, reported to `on_progress`.

    TRANSCRIBING and PUNCTUATING are each a single opaque call -- `on_progress` fires with
    `total=0` on entry (indeterminate: show the stage label, not a moving bar) and `(1, 1)` on
    completion. IDENTIFYING_SPEAKERS and REMOVING_BACKCHANNELS are each itemized (per utterance,
    per LLM batch respectively) and report real `(completed, total)` throughout.
    """

    TRANSCRIBING = "transcribing"
    IDENTIFYING_SPEAKERS = "identifying_speakers"
    PUNCTUATING = "punctuating"
    REMOVING_BACKCHANNELS = "removing_backchannels"


OnProgress = Callable[[Stage, int, int], None]


@dataclass(frozen=True)
class TranscriptionResult:
    """The outcome of a transcription run, for the caller to report to the user."""

    utterance_count: int
    unassigned_speaker_count: int
    removed_backchannel_count: int


def can_transcribe_audio(session: Session, session_id: uuid.UUID, session_folder: Path) -> tuple[bool, str | None]:
    """One shared precondition check, usable both for `T`'s enabled/disabled UI state and as a guard inside `transcribe_audio` itself.

    Audio preparation requires an input recording and attendees, but does not require
    every attendee to already have a voice profile. Bootstrap processing persists raw
    diarization and gathers identity evidence before later speaker identification.
    """
    if not session_artifacts(session_folder)[ArtifactName.INPUT_AUDIO]:
        return False, "Import input audio first."

    attendees = list_attendance(session, session_id)
    if not attendees:
        return False, "Add attendees before transcribing."

    return True, None


def transcribe_audio(
    session_folder: Path,
    centroids: dict[str, Embedding],
    embed: EmbeddingFactory,
    transcription_settings: TranscriptionAndDiarizationSettings,
    speaker_id_settings: SpeakerIdentificationSettings,
    backchannel_settings: RemoveBackchannelsSettings,
    llm_model_lite: str,
    on_progress: OnProgress | None = None,
) -> TranscriptionResult:
    """Transcribe, diarize, identify speakers, punctuate, and remove backchannels from a session's input audio.

    Reads `input_audio.wav` from `session_folder` and writes `transcript.json`
    (the tablesage_tools `Transcript`, machine-readable) and `transcript.md` (a
    timestamped, speaker-labeled script for humans) there, only once every stage has
    succeeded -- a failure partway through leaves no artifacts behind, matching
    `import_audio`'s all-or-nothing contract. `centroids` should be scoped to
    the session's attendees; its size is passed through to diarization as the
    expected speaker count, since `identify_speakers` already assumes exactly
    that correspondence.

    Backchannel removal here is the pre-review pass -- unconditional, no settings toggle, since
    easier Manual Review applies to every session. It judges every wordlist-matched candidate via
    a batched LLM call regardless of speaker (see `remove_backchannels.py`); the post-review pass
    (`session_pipeline.clean_transcript`) is a separate, simpler, LLM-free mechanical filter.
    Role-name rendering is not part of transcription either -- see `clean_transcript`.
    """
    raw_transcript = transcribe_and_diarize_audio(session_folder, len(centroids), transcription_settings, on_progress)
    return identify_and_publish_transcript(
        session_folder,
        raw_transcript,
        centroids,
        embed,
        speaker_id_settings,
        backchannel_settings,
        llm_model_lite,
        on_progress,
    )


def transcribe_and_diarize_audio(
    session_folder: Path,
    attendee_count: int,
    transcription_settings: TranscriptionAndDiarizationSettings,
    on_progress: OnProgress | None = None,
) -> Transcript:
    """Return anonymous raw diarization without publishing a canonical transcript."""
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename

    async def _run() -> Transcript:
        _report(on_progress, Stage.TRANSCRIBING, 0, 0)
        transcript = await transcribe_and_diarize(
            audio_path,
            transcription_settings.language_code,
            transcription_settings.model_id,
            transcription_settings.timeout,
            transcription_settings.tag_audio_events,
            attendee_count,
        )
        _report(on_progress, Stage.TRANSCRIBING, 1, 1)
        return transcript

    return asyncio.run(_run())


def identify_raw_transcript(
    session_folder: Path,
    transcript: Transcript,
    centroids: dict[str, Embedding],
    embed: EmbeddingFactory,
    speaker_id_settings: SpeakerIdentificationSettings,
    *,
    absolute_similarity_threshold: float | None = None,
    force_abstention: bool = False,
    on_progress: OnProgress | None = None,
) -> Transcript:
    """Identify a raw transcript without punctuation, backchannel removal, or publication."""

    async def _run() -> Transcript:
        if not centroids:
            return transcript.model_copy(
                update={
                    "utterances": [
                        utterance.model_copy(update={"speaker": UNASSIGNED_SPEAKER, "similarity_margin": 0.0})
                        for utterance in transcript.utterances
                    ]
                }
            )

        def progress(completed: int, total: int) -> None:
            _report(on_progress, Stage.IDENTIFYING_SPEAKERS, completed, total)

        return await identify_speakers(
            transcript,
            session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename,
            centroids,
            embed,
            speaker_id_settings.similarity_margin_threshold,
            progress,
            duration_override_min_seconds=speaker_id_settings.duration_override.min_seconds,
            duration_override_similarity_margin_threshold=speaker_id_settings.duration_override.similarity_margin_threshold,
            short_utterance_widening=None
            if force_abstention
            else ShortUtteranceWideningConfig(
                max_original_duration_seconds=speaker_id_settings.short_utterance_widening.max_original_duration_seconds,
                target_duration_seconds=speaker_id_settings.short_utterance_widening.target_duration_seconds,
                max_neighbor_gap_seconds=speaker_id_settings.short_utterance_widening.max_neighbor_gap_seconds,
            )
            if speaker_id_settings.short_utterance_widening.enabled
            else None,
            # Propagation is intentionally disabled for bootstrap: it must not bypass an
            # absolute or relative rejection in an incomplete-reference session.
            cluster_propagation=None
            if force_abstention
            else ClusterPropagationConfig(
                evidence_min_duration_seconds=speaker_id_settings.cluster_propagation.evidence_min_duration_seconds,
                max_utterance_duration_seconds=speaker_id_settings.cluster_propagation.max_utterance_duration_seconds,
                cluster_margin_threshold=speaker_id_settings.cluster_propagation.cluster_margin_threshold,
                contradiction_veto_margin_threshold=speaker_id_settings.cluster_propagation.contradiction_veto_margin_threshold,
            )
            if speaker_id_settings.cluster_propagation.enabled
            else None,
            log_diagnostics=speaker_id_settings.log_diagnostics,
            allow_unassigned=True if force_abstention else speaker_id_settings.allow_unassigned,
            absolute_similarity_threshold=absolute_similarity_threshold,
        )

    return asyncio.run(_run())


def identify_and_publish_transcript(
    session_folder: Path,
    transcript: Transcript,
    centroids: dict[str, Embedding],
    embed: EmbeddingFactory,
    speaker_id_settings: SpeakerIdentificationSettings,
    backchannel_settings: RemoveBackchannelsSettings,
    llm_model_lite: str,
    on_progress: OnProgress | None = None,
) -> TranscriptionResult:
    """Identify, punctuate, and publish a canonical transcript from raw diarization.

    The current identifier uses a relative best/runner-up comparison. With fewer than two
    references it cannot make a safe judgment, so this phase preserves unresolved rows for
    human review instead of failing or guessing.
    """

    working_transcript = transcript

    async def _run() -> tuple[Transcript, int]:
        nonlocal working_transcript

        def _identify_progress(completed: int, total: int) -> None:
            _report(on_progress, Stage.IDENTIFYING_SPEAKERS, completed, total)

        # Preserve the existing one-reference path until Phase 3 supplies its
        # calibrated conservative fallback.  The no-reference bootstrap case
        # must still abstain rather than inventing an assignment.
        if centroids:
            audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
            working_transcript = await identify_speakers(
                working_transcript,
                audio_path,
                centroids,
                embed,
                speaker_id_settings.similarity_margin_threshold,
                _identify_progress,
                duration_override_min_seconds=speaker_id_settings.duration_override.min_seconds,
                duration_override_similarity_margin_threshold=(speaker_id_settings.duration_override.similarity_margin_threshold),
                short_utterance_widening=(
                    ShortUtteranceWideningConfig(
                        max_original_duration_seconds=(speaker_id_settings.short_utterance_widening.max_original_duration_seconds),
                        target_duration_seconds=(speaker_id_settings.short_utterance_widening.target_duration_seconds),
                        max_neighbor_gap_seconds=(speaker_id_settings.short_utterance_widening.max_neighbor_gap_seconds),
                    )
                    if speaker_id_settings.short_utterance_widening.enabled
                    else None
                ),
                cluster_propagation=(
                    ClusterPropagationConfig(
                        evidence_min_duration_seconds=(speaker_id_settings.cluster_propagation.evidence_min_duration_seconds),
                        max_utterance_duration_seconds=(speaker_id_settings.cluster_propagation.max_utterance_duration_seconds),
                        cluster_margin_threshold=(speaker_id_settings.cluster_propagation.cluster_margin_threshold),
                        contradiction_veto_margin_threshold=(speaker_id_settings.cluster_propagation.contradiction_veto_margin_threshold),
                    )
                    if speaker_id_settings.cluster_propagation.enabled
                    else None
                ),
                log_diagnostics=speaker_id_settings.log_diagnostics,
                allow_unassigned=speaker_id_settings.allow_unassigned,
            )
        else:
            _report(on_progress, Stage.IDENTIFYING_SPEAKERS, 0, 0)
            working_transcript = working_transcript.model_copy(
                update={
                    "utterances": [
                        utterance.model_copy(update={"speaker": UNASSIGNED_SPEAKER, "similarity_margin": 0.0})
                        for utterance in working_transcript.utterances
                    ]
                }
            )
            _report(on_progress, Stage.IDENTIFYING_SPEAKERS, 1, 1)

        _report(on_progress, Stage.PUNCTUATING, 0, 0)
        working_transcript = await punctuate_transcript(working_transcript)
        _report(on_progress, Stage.PUNCTUATING, 1, 1)

        pre_backchannel_count = len(working_transcript.utterances)

        def _backchannel_progress(completed: int, total: int) -> None:
            _report(on_progress, Stage.REMOVING_BACKCHANNELS, completed, total)

        working_transcript = await remove_backchannels(
            working_transcript,
            backchannel_settings.max_words,
            llm_model_lite,
            backchannel_settings.question_check_timeout,
            backchannel_settings.batch_size,
            backchannel_settings.max_concurrent_batches,
            on_progress=_backchannel_progress,
        )
        removed_backchannel_count = pre_backchannel_count - len(working_transcript.utterances)

        return working_transcript, removed_backchannel_count

    with widelog.wide_event(op="identify_and_publish_transcript", session_folder=str(session_folder), speaker_count=len(centroids)) as log:
        transcript, removed_backchannel_count = asyncio.run(_run())

        transcript.save(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
        (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_TEXT].filename).write_text(
            _render_transcript_text(transcript), encoding="utf-8"
        )
        unassigned_count = sum(1 for utterance in transcript.utterances if utterance.speaker == UNASSIGNED_SPEAKER)
        log.set(
            utterance_count=len(transcript.utterances),
            unassigned_speaker_count=unassigned_count,
            removed_backchannel_count=removed_backchannel_count,
        )
        return TranscriptionResult(
            utterance_count=len(transcript.utterances),
            unassigned_speaker_count=unassigned_count,
            removed_backchannel_count=removed_backchannel_count,
        )


def _report(on_progress: OnProgress | None, stage: Stage, completed: int, total: int) -> None:
    if on_progress is not None:
        on_progress(stage, completed, total)


def _render_transcript_text(transcript: Transcript) -> str:
    return "\n\n".join(_render_utterance(utterance) for utterance in transcript.utterances) + "\n"


def _render_utterance(utterance: Utterance) -> str:
    text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
    return f"[{_format_timestamp(utterance.start)}] **{utterance.speaker}:** {text}"


def _format_timestamp(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
