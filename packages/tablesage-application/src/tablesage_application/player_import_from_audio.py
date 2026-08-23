from __future__ import annotations

import asyncio
import shutil
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from sqlmodel import Session
from tablesage_model.settings import EnhanceVoicesSettings, RemoveOutliersSettings, TranscriptionAndDiarizationSettings
from tablesage_tools.audio import clean_clip, convert_to_16k_mono, extract_clip
from tablesage_tools.embeddings import Embedding, SimilarityComputer, compute_centroid
from tablesage_tools.model import Transcript, Utterance
from tablesage_tools.punctuation import punctuate_transcript
from tablesage_tools.transcription import transcribe_and_diarize

from .voice_clips import clips


class Stage(Enum):
    """A player-import-from-audio pipeline stage, reported to `on_progress`.

    CLEANING/TRANSCRIBING/PUNCTUATING/PROPOSING_ATTENDEES are each a single opaque call
    -- `on_progress` fires with `total=0` on entry (indeterminate) and `(1, 1)` on
    completion, mirroring `session_pipeline.transcribe_audio.Stage`. EXTRACTING_SPEAKER_CLIPS,
    WRITING_CLIPS, and RECOMPUTING_CENTROIDS are itemized and report real `(completed, total)`
    throughout, mirroring `players_from_session.Stage`.
    """

    CLEANING = "cleaning"
    TRANSCRIBING = "transcribing"
    PUNCTUATING = "punctuating"
    EXTRACTING_SPEAKER_CLIPS = "extracting_speaker_clips"
    PROPOSING_ATTENDEES = "proposing_attendees"
    WRITING_CLIPS = "writing_clips"
    RECOMPUTING_CENTROIDS = "recomputing_centroids"


OnProgress = Callable[[Stage, int, int], None]


def _report(on_progress: OnProgress | None, stage: Stage, completed: int, total: int) -> None:
    if on_progress is not None:
        on_progress(stage, completed, total)


# --- Stage 2: clean, transcribe, diarize, punctuate ---


def transcribe_audio_file(
    source_audio_path: Path,
    cleaned_audio_path: Path,
    normalize_volume: bool,
    transcription_settings: TranscriptionAndDiarizationSettings,
    speaker_count: int | None,
    on_progress: OnProgress | None = None,
    *,
    should_clean_audio: bool = True,
) -> Transcript:
    """Clean, transcribe+diarize, and punctuate a standalone audio file into a speaker-labeled `Transcript`.

    Mirrors `session_pipeline.transcribe_audio.transcribe_audio`'s shape, but cleans into
    `cleaned_audio_path` (a run-scoped temp file, not a session folder -- this flow has no
    session yet) and has no attendee centroids to pass as an expected-speaker-count fallback:
    `speaker_count` is a wizard input the user optionally supplies directly.

    `should_clean_audio=False` skips the Mossformer2 noise-removal pass (and, since it's
    part of the same call, `normalize_volume` with it) entirely -- a plain format
    conversion still runs, so `cleaned_audio_path` is always a valid 16kHz mono wav either
    way, matching `clean_clip`'s own guaranteed output format for every downstream stage.
    """

    async def _run() -> Transcript:
        _report(on_progress, Stage.CLEANING, 0, 0)
        if should_clean_audio:
            await clean_clip(source_audio_path, cleaned_audio_path, normalize=normalize_volume)
        else:
            await convert_to_16k_mono(source_audio_path, cleaned_audio_path)
        _report(on_progress, Stage.CLEANING, 1, 1)

        _report(on_progress, Stage.TRANSCRIBING, 0, 0)
        transcript = await transcribe_and_diarize(
            cleaned_audio_path,
            transcription_settings.language_code,
            transcription_settings.model_id,
            transcription_settings.timeout,
            transcription_settings.tag_audio_events,
            speaker_count,
        )
        _report(on_progress, Stage.TRANSCRIBING, 1, 1)

        _report(on_progress, Stage.PUNCTUATING, 0, 0)
        transcript = await punctuate_transcript(transcript)
        _report(on_progress, Stage.PUNCTUATING, 1, 1)
        return transcript

    return asyncio.run(_run())


# --- Stage 3: per-speaker aggregation, centroids, existing-player match, LLM proposal ---


@dataclass(frozen=True)
class SpeakerCandidate:
    """One pre-step name+roles guess the user supplies before transcription, to help the LLM guess (Stage 3).

    `roles` (plural) matches `Attendee.roles`'s shape -- multiple roles per candidate,
    same as a real attendee can hold. Only ever joined into one display string for the
    LLM prompt hint (see `Application.import_players_from_audio_propose`); nothing else
    in this flow needs them separately.
    """

    name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class SpeakerUtteranceClip:
    utterance: Utterance
    clip_path: Path


@dataclass(frozen=True)
class SpeakerProposal:
    """One diarized speaker's proposed resolution, before human review (Stage 4).

    `suggested_role` is always `""` -- the LLM is no longer asked for a role (see
    `SpeakerGuess`), only a name and a confidence. The review screen's role field simply
    starts blank for an LLM-driven proposal now.
    """

    speaker_id: str
    utterance_count: int
    transcript_text: str
    suggested_name: str
    suggested_role: str
    suggested_confidence: str | None
    matched_player_id: uuid.UUID | None
    matched_player_name: str | None


@dataclass(frozen=True)
class ProposeResult:
    proposals: tuple[SpeakerProposal, ...]
    speaker_clips: dict[str, tuple[SpeakerUtteranceClip, ...]]
    speaker_centroids: dict[str, Embedding]


class SpeakerGuess(BaseModel):
    speaker_label: str
    player: str
    confidence: Literal["low", "medium", "high"]


class SpeakerGuesses(BaseModel):
    """The LLM's proposed player+confidence per diarized speaker label -- schema for
    `call_llm_with_prompt`'s `response_model`, matching `_prompts/propose_speakers/system.md`'s
    `<output_format>` exactly (field names, field order, and `scratchpad` first).

    `scratchpad` gives the model a place to reason before committing to `speakers` --
    schema-constrained structured output only guarantees the *shape* of a response, not
    room for chain-of-thought outside it, so the reasoning has to be a field in the schema
    itself, ordered first, rather than free prose before/after a JSON block. Its content is
    never read by this app; it exists purely to give the model somewhere to think.
    """

    scratchpad: str
    speakers: list[SpeakerGuess]


@dataclass(frozen=True)
class SpeakerProposalPromptData:
    """`template_data` for `PromptName.PROPOSE_SPEAKERS` -- see `_prompts/propose_speakers/template.j2`."""

    speakers: list[dict[str, str]]
    candidates: list[dict[str, str]]


# Injected: per-speaker (speaker_id, transcript_text) pairs plus the pre-step candidate list,
# in; a player+confidence guess per speaker_id, out. Wraps `call_llm_with_prompt` + `PromptName`
# + `SpeakerGuesses` parsing at the Application layer, kept out of this module so it stays
# unit-testable without litellm.
ProposeSpeakers = Callable[[list[tuple[str, str]], list[SpeakerCandidate]], list[SpeakerGuess]]

# The literal sentinel `system.md` instructs the model to use for "couldn't determine a
# name" -- matched case-insensitively, never surfaced to the user as if it were a real name.
_UNASSIGNED_GUESS = "unassigned speaker"


def _utterances_by_speaker(transcript: Transcript) -> dict[str, list[Utterance]]:
    by_speaker: dict[str, list[Utterance]] = {}
    for utterance in transcript.utterances:
        by_speaker.setdefault(utterance.speaker, []).append(utterance)
    return by_speaker


def _suggested_name(speaker_id: str, guesses: dict[str, SpeakerGuess]) -> str:
    """The LLM's guessed player name, or the raw diarized `speaker_id` itself when there's no
    guess to show -- a visibly synthetic placeholder ("speaker_0") beats silently showing the
    model's own "unassigned speaker" sentinel as if it were a real name."""
    guess = guesses.get(speaker_id)
    if guess is None or guess.player.strip().lower() == _UNASSIGNED_GUESS:
        return speaker_id
    return guess.player


def propose_attendees(
    cleaned_audio_path: Path,
    clip_dir: Path,
    transcript: Transcript,
    candidates: list[SpeakerCandidate],
    existing_player_centroids: dict[uuid.UUID, tuple[str, Embedding]],
    embed: Callable[[Path], Embedding],
    propose_speakers: ProposeSpeakers,
    similarity_margin_threshold: float,
    on_progress: OnProgress | None = None,
) -> ProposeResult:
    """Aggregate a diarized `Transcript` by speaker, extract each speaker's clips once, and propose an attendee map.

    Extraction happens once here, into `clip_dir` (a run-scoped temp directory the caller
    owns and cleans up) -- Stage 5 reuses these same clip files by copy, never re-extracting.
    The two matching signals are independent and never conflated (see the design doc): the
    existing-player match is skipped entirely, not approximated, when fewer than two existing
    players have a computed centroid (`SimilarityComputer` requires at least two references).
    """
    by_speaker = _utterances_by_speaker(transcript)
    speaker_ids = list(by_speaker)  # dict insertion order == first-appearance order in the transcript

    total_clips = sum(len(utterances) for utterances in by_speaker.values())
    completed = 0
    _report(on_progress, Stage.EXTRACTING_SPEAKER_CLIPS, 0, total_clips)

    async def _extract_all() -> dict[str, list[SpeakerUtteranceClip]]:
        nonlocal completed
        result: dict[str, list[SpeakerUtteranceClip]] = {}
        for speaker_id in speaker_ids:
            speaker_clips: list[SpeakerUtteranceClip] = []
            for index, utterance in enumerate(by_speaker[speaker_id]):
                clip_path = clip_dir / f"{speaker_id}-{index}.wav"
                await extract_clip(cleaned_audio_path, clip_path, utterance.start, utterance.end)
                speaker_clips.append(SpeakerUtteranceClip(utterance=utterance, clip_path=clip_path))
                completed += 1
                _report(on_progress, Stage.EXTRACTING_SPEAKER_CLIPS, completed, total_clips)
            result[speaker_id] = speaker_clips
        return result

    speaker_clips = asyncio.run(_extract_all())

    speaker_centroids: dict[str, Embedding] = {
        speaker_id: compute_centroid([clip.clip_path for clip in speaker_clips[speaker_id]], embed).centroid for speaker_id in speaker_ids
    }

    matches: dict[str, tuple[uuid.UUID, str]] = {}
    if len(existing_player_centroids) >= 2:
        player_ids = list(existing_player_centroids)
        computer = SimilarityComputer(tuple(existing_player_centroids[player_id][1] for player_id in player_ids))
        for speaker_id in speaker_ids:
            result = computer.compute_similarity(speaker_centroids[speaker_id])
            if result.margin >= similarity_margin_threshold:
                matched_id = player_ids[result.best_match_index]
                matches[speaker_id] = (matched_id, existing_player_centroids[matched_id][0])

    speaker_texts: dict[str, str] = {
        speaker_id: " ".join(utterance.punctuated_text or utterance.text for utterance in by_speaker[speaker_id])
        for speaker_id in speaker_ids
    }

    _report(on_progress, Stage.PROPOSING_ATTENDEES, 0, 0)
    guesses = {guess.speaker_label: guess for guess in propose_speakers([(sid, speaker_texts[sid]) for sid in speaker_ids], candidates)}
    _report(on_progress, Stage.PROPOSING_ATTENDEES, 1, 1)

    proposals = tuple(
        SpeakerProposal(
            speaker_id=speaker_id,
            utterance_count=len(by_speaker[speaker_id]),
            transcript_text=speaker_texts[speaker_id],
            suggested_name=_suggested_name(speaker_id, guesses),
            suggested_role="",
            suggested_confidence=guesses[speaker_id].confidence if speaker_id in guesses else None,
            matched_player_id=matches[speaker_id][0] if speaker_id in matches else None,
            matched_player_name=matches[speaker_id][1] if speaker_id in matches else None,
        )
        for speaker_id in speaker_ids
    )

    return ProposeResult(
        proposals=proposals,
        speaker_clips={speaker_id: tuple(speaker_clips[speaker_id]) for speaker_id in speaker_ids},
        speaker_centroids=speaker_centroids,
    )


# --- Stage 5/6: build/enhance players from the human-confirmed attendee map ---


@dataclass(frozen=True)
class PendingResolution:
    """One human-confirmed, non-excluded Stage 4 row, before "New Player" rows are created.

    `player_id` is `None` for a "New Player" row -- the Application layer creates that
    `Player` (folder starts empty) before this becomes a `ResolvedSpeaker`.
    """

    speaker_id: str
    player_id: uuid.UUID | None
    player_name: str
    role: str


@dataclass(frozen=True)
class ResolvedSpeaker:
    """One human-confirmed, non-excluded row from Stage 4's review table, with its `Player` already resolved."""

    speaker_id: str
    player_id: uuid.UUID
    player_name: str
    role: str


@dataclass(frozen=True)
class AttendeeSummary:
    """One line of Stage 7's read-only summary."""

    player_name: str
    role: str
    clip_count: int


@dataclass(frozen=True)
class ImportFromAudioResult:
    affected_player_count: int
    clip_count: int
    summary: tuple[AttendeeSummary, ...]


def _generated_diarized_filename(player_name: str, source_hash: str) -> str:
    return f"diarized-{clips.slugify(player_name)}-{source_hash}-{uuid.uuid4().hex}.wav"


def build_players_from_audio(
    session: Session,
    source_audio_path: Path,
    speaker_clips: Mapping[str, Sequence[SpeakerUtteranceClip]],
    speaker_centroids: dict[str, Embedding],
    resolved: list[ResolvedSpeaker],
    player_folders: dict[uuid.UUID, Path],
    embed: Callable[[Path], Embedding],
    enhance_settings: EnhanceVoicesSettings,
    outlier_settings: RemoveOutliersSettings,
    on_progress: OnProgress | None = None,
) -> ImportFromAudioResult:
    """Write qualifying clips into each resolved player's folder and recompute their centroids.

    Reuses `speaker_clips`' already-extracted files by copy (never re-extracts). The
    post-review clip-quality gate (comparing each candidate clip against this run's own
    finalized speaker centroids) only runs when at least two speakers were confirmed this
    run -- with exactly one, there is no sibling to disambiguate against, so every
    duration-valid clip is kept (see the design doc's below-floor fallback). Filenames use a
    `diarized-<player_slug>-<sourcehash8>-<uuid4>.wav` convention, matching directory
    import's `import-...` and "enhance from session"'s `session-...` conventions
    (`find_clips_by_hash_segment`); re-running against the same source file replaces that
    file's prior contribution to each player as a unit -- copy-then-delete, so a bad rerun
    never leaves a player with fewer samples than before.
    """
    source_hash = clips.hash8(str(source_audio_path.resolve()))

    gate_computer: SimilarityComputer | None = None
    speaker_index: dict[str, int] = {}
    if len(resolved) >= 2:
        speaker_index = {attendee.speaker_id: index for index, attendee in enumerate(resolved)}
        gate_computer = SimilarityComputer(tuple(speaker_centroids[attendee.speaker_id] for attendee in resolved))

    total_candidates = sum(len(speaker_clips.get(attendee.speaker_id, ())) for attendee in resolved)
    completed = 0
    written_counts: dict[uuid.UUID, int] = {}
    _report(on_progress, Stage.WRITING_CLIPS, 0, total_candidates)

    for attendee in resolved:
        folder = player_folders[attendee.player_id]
        folder.mkdir(parents=True, exist_ok=True)
        prior_clips = clips.find_clips_by_hash_segment(folder, "diarized", source_hash)

        written = 0
        for candidate in speaker_clips.get(attendee.speaker_id, ()):
            duration = candidate.utterance.end - candidate.utterance.start
            qualifies = enhance_settings.min_clip_seconds <= duration <= enhance_settings.max_clip_seconds
            if qualifies and gate_computer is not None:
                result = gate_computer.compute_similarity(embed(candidate.clip_path))
                qualifies = result.best_match_index == speaker_index[attendee.speaker_id]
                qualifies = qualifies and result.margin >= enhance_settings.min_margin_for_voice_sample

            completed += 1
            _report(on_progress, Stage.WRITING_CLIPS, completed, total_candidates)
            if not qualifies:
                continue

            filename = _generated_diarized_filename(attendee.player_name, source_hash)
            shutil.copyfile(candidate.clip_path, folder / filename)
            written += 1

        for old_clip in prior_clips:
            old_clip.unlink(missing_ok=True)

        written_counts[attendee.player_id] = written

    for index, attendee in enumerate(resolved, start=1):
        folder = player_folders[attendee.player_id]
        clips.recompute_centroid(
            session, attendee.player_id, folder, embed, None, outlier_settings.min_sample_similarity, outlier_settings.min_samples
        )
        _report(on_progress, Stage.RECOMPUTING_CENTROIDS, index, len(resolved))

    affected_player_count = sum(1 for count in written_counts.values() if count > 0)
    summary = tuple(
        AttendeeSummary(player_name=attendee.player_name, role=attendee.role, clip_count=written_counts[attendee.player_id])
        for attendee in resolved
    )
    return ImportFromAudioResult(affected_player_count=affected_player_count, clip_count=sum(written_counts.values()), summary=summary)
