from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import widelog
from sqlmodel import Session
from tablesage_model.model import Player
from tablesage_model.settings import RemoveBackchannelsSettings, SpeakerIdentificationSettings, TranscriptionAndDiarizationSettings
from tablesage_tools.embeddings import Embedding, EmbeddingFactory
from tablesage_tools.model import Transcript, Utterance
from tablesage_tools.punctuation import punctuate_transcript
from tablesage_tools.speakers import UNASSIGNED_SPEAKER, identify_speakers
from tablesage_tools.transcription import transcribe_and_diarize

from ..entities.sessions import list_attendance
from ..paths import ARTIFACTS, ArtifactName
from .artifacts import session_artifacts
from .remove_backchannels import remove_backchannels


class Stage(Enum):
    """A `transcribe_audio` pipeline stage, reported to `on_progress`.

    TRANSCRIBING, PUNCTUATING, and REMOVING_BACKCHANNELS are each a single opaque call --
    `on_progress` fires with `total=0` on entry (indeterminate: show the stage label, not a
    moving bar) and `(1, 1)` on completion. IDENTIFYING_SPEAKERS is itemized per utterance and
    reports real `(completed, total)` throughout. REMOVING_BACKCHANNELS is only reported when
    `backchannel_settings.enabled` is true -- it never fires at all otherwise.
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


def can_transcribe_audio(session: Session, session_id: uuid.UUID, session_folder: Path) -> tuple[bool, str | None]:
    """One shared precondition check, usable both for `T`'s enabled/disabled UI state and as a guard inside `transcribe_audio` itself.

    Mirrors `can_process_session`'s shape (and its "Missing voice profile"
    check) rather than just gating on attendee count: `identify_speakers`
    raises if handed fewer than 2 centroids, so an attendee without a
    computed voice profile must block here too, not surface as a failure
    only after minutes of real transcription API time have already been spent.
    """
    if not session_artifacts(session_folder)[ArtifactName.INPUT_AUDIO]:
        return False, "Import input audio first."

    attendees = list_attendance(session, session_id)
    if not attendees:
        return False, "Add attendees before transcribing."

    missing = [attendee.player_name for attendee in attendees if not _player_has_centroid(session, attendee.player_id)]
    if missing:
        return False, f"Missing voice profile for: {', '.join(missing)}."
    return True, None


def _player_has_centroid(session: Session, player_id: uuid.UUID) -> bool:
    player = session.get(Player, player_id)
    return player is not None and player.centroid_embedding is not None


def transcribe_audio(
    session_folder: Path,
    centroids: dict[str, Embedding],
    role_names: dict[str, str],
    embed: EmbeddingFactory,
    transcription_settings: TranscriptionAndDiarizationSettings,
    speaker_id_settings: SpeakerIdentificationSettings,
    backchannel_settings: RemoveBackchannelsSettings | None = None,
    llm_model_lite: str = "anthropic/claude-haiku-4-5",
    on_progress: OnProgress | None = None,
) -> TranscriptionResult:
    """Transcribe, diarize, identify speakers, punctuate, and (optionally) remove backchannels from a session's input audio.

    Reads `input_audio.wav` from `session_folder` and writes `transcript.json`
    (the tablesage_tools `Transcript`, machine-readable), `transcript.md` (a
    timestamped, speaker-labeled script for humans), and `transcript_roles.md`
    (the same script with each speaker's name swapped for their in-session
    role, for LLM consumption) there, only once every stage has succeeded --
    a failure partway through leaves no artifacts behind, matching
    `import_audio`'s all-or-nothing contract. `centroids` should be scoped to
    the session's attendees; its size is passed through to diarization as the
    expected speaker count, since `identify_speakers` already assumes exactly
    that correspondence. `role_names` maps each attendee's player name to
    their first (alphabetically) role name that session; a speaker missing
    from it (including `UNASSIGNED_SPEAKER`) is left as-is in
    `transcript_roles.md`. When `backchannel_settings.enabled` is false (the
    default), the REMOVING_BACKCHANNELS stage is skipped entirely --
    `on_progress` never fires for it and `llm_model_lite` is never called.
    """
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
    backchannel_settings = backchannel_settings if backchannel_settings is not None else RemoveBackchannelsSettings()

    async def _run() -> Transcript:
        _report(on_progress, Stage.TRANSCRIBING, 0, 0)
        transcript = await transcribe_and_diarize(
            audio_path,
            transcription_settings.language_code,
            transcription_settings.model_id,
            transcription_settings.timeout,
            transcription_settings.tag_audio_events,
            len(centroids),
        )
        _report(on_progress, Stage.TRANSCRIBING, 1, 1)

        def _identify_progress(completed: int, total: int) -> None:
            _report(on_progress, Stage.IDENTIFYING_SPEAKERS, completed, total)

        transcript = await identify_speakers(
            transcript,
            audio_path,
            centroids,
            embed,
            speaker_id_settings.similarity_margin_threshold,
            _identify_progress,
            log_diagnostics=speaker_id_settings.log_diagnostics,
        )

        _report(on_progress, Stage.PUNCTUATING, 0, 0)
        transcript = await punctuate_transcript(transcript)
        _report(on_progress, Stage.PUNCTUATING, 1, 1)

        if backchannel_settings.enabled:
            _report(on_progress, Stage.REMOVING_BACKCHANNELS, 0, 0)
            transcript = await remove_backchannels(transcript, backchannel_settings.max_words, llm_model_lite)
            _report(on_progress, Stage.REMOVING_BACKCHANNELS, 1, 1)

        return transcript

    with widelog.wide_event(op="transcribe_audio", session_folder=str(session_folder), speaker_count=len(centroids)) as log:
        transcript = asyncio.run(_run())

        transcript.save(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
        (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_TEXT].filename).write_text(
            _render_transcript_text(transcript), encoding="utf-8"
        )
        (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename).write_text(
            _render_transcript_text(transcript, role_names), encoding="utf-8"
        )

        unassigned_count = sum(1 for utterance in transcript.utterances if utterance.speaker == UNASSIGNED_SPEAKER)
        log.set(utterance_count=len(transcript.utterances), unassigned_speaker_count=unassigned_count)
        return TranscriptionResult(utterance_count=len(transcript.utterances), unassigned_speaker_count=unassigned_count)


def _report(on_progress: OnProgress | None, stage: Stage, completed: int, total: int) -> None:
    if on_progress is not None:
        on_progress(stage, completed, total)


def _render_transcript_text(transcript: Transcript, role_names: dict[str, str] | None = None) -> str:
    return "\n\n".join(_render_utterance(utterance, role_names) for utterance in transcript.utterances) + "\n"


def _render_utterance(utterance: Utterance, role_names: dict[str, str] | None = None) -> str:
    text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
    speaker = utterance.speaker
    if role_names is not None and speaker != UNASSIGNED_SPEAKER:
        speaker = role_names.get(speaker, speaker)
    return f"[{_format_timestamp(utterance.start)}] **{speaker}:** {text}"


def _format_timestamp(seconds: float) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
