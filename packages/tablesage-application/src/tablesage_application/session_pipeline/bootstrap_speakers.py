"""Transcript-backed identity evidence for attendees without a usable voice profile."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel
from tablesage_model.settings import SpeakerBootstrapSettings
from tablesage_tools.model import Transcript, Utterance

from ..llm import PromptName, call_llm_with_prompt
from .bootstrap_workflow import BootstrapAttendeeSnapshot, SourceUtteranceId


class BootstrapEvidenceClaimResponse(BaseModel, frozen=True):
    player_id: uuid.UUID
    diarized_speaker_id: str
    candidate_utterance_indices: tuple[int, ...]
    evidence_utterance_indices: tuple[int, ...]
    explanation: str


class BootstrapEvidenceResponse(BaseModel, frozen=True):
    claims: tuple[BootstrapEvidenceClaimResponse, ...]


class BootstrapEvidenceClaim(BaseModel, frozen=True):
    player_id: uuid.UUID
    diarized_speaker_id: str
    candidate_utterance_ids: tuple[SourceUtteranceId, ...]
    evidence_utterance_ids: tuple[SourceUtteranceId, ...]
    explanation: str


class BootstrapEvidence(BaseModel, frozen=True):
    claims: tuple[BootstrapEvidenceClaim, ...]


class DiarizedBootstrapTranscript(BaseModel, frozen=True):
    """Raw diarization plus stable IDs, persisted before LLM evidence inference begins."""

    run_id: uuid.UUID
    transcript: Transcript
    utterance_ids: tuple[SourceUtteranceId, ...]


class BootstrapPreparationResult(BaseModel, frozen=True):
    run_id: uuid.UUID | None
    raw_transcript: Transcript
    evidence: BootstrapEvidence


class BootstrapSeedDiagnostic(BaseModel, frozen=True):
    utterance_id: SourceUtteranceId
    accepted: bool
    reason: str | None
    leave_one_out_similarity: float | None
    competitor_similarity: float | None
    competitor_margin: float | None


class BootstrapSeedSelection(BaseModel, frozen=True):
    player_id: uuid.UUID
    selected_utterance_ids: tuple[SourceUtteranceId, ...]
    centroid: tuple[float, ...] | None
    diagnostics: tuple[BootstrapSeedDiagnostic, ...]
    reason: str | None
    independent_exchange_count: int
    total_speech_seconds: float


class BootstrapSelectionResult(BaseModel, frozen=True):
    selections: tuple[BootstrapSeedSelection, ...]
    collision_player_pairs: tuple[tuple[uuid.UUID, uuid.UUID], ...]


class BootstrapCandidateReview(BaseModel, frozen=True):
    """Human-approved candidate claims; omitted claims are explicitly unresolved."""

    evidence: BootstrapEvidence


@dataclass(frozen=True)
class _PromptUtterance:
    index: int
    speaker_id: str
    text: str


@dataclass(frozen=True)
class _PromptData:
    attendees: Sequence[BootstrapAttendeeSnapshot]
    utterances: Sequence[_PromptUtterance]


EvidenceCaller = Callable[[PromptName, object, str, type[BaseModel], float], Awaitable[str]]


def speech_duration(utterance: Utterance) -> float:
    """Speech duration from the union of word intervals, excluding gaps."""
    intervals = sorted((word.start, word.end) for word in utterance.words if word.end > word.start)
    if not intervals:
        return 0.0
    total = 0.0
    start, end = intervals[0]
    for next_start, next_end in intervals[1:]:
        if next_start > end:
            total += end - start
            start, end = next_start, next_end
        else:
            end = max(end, next_end)
    return total + end - start


def has_cross_speaker_overlap(transcript: Transcript, utterance_index: int) -> bool:
    """Detect observable crosstalk from word timestamps on a different diarized label."""
    utterance = transcript.utterances[utterance_index]
    for word in utterance.words:
        for other_index, other in enumerate(transcript.utterances):
            if other_index == utterance_index or other.speaker == utterance.speaker:
                continue
            if any(word.start < other_word.end and other_word.start < word.end for other_word in other.words):
                return True
    return False


async def propose_bootstrap_evidence(
    raw: DiarizedBootstrapTranscript,
    targets: Sequence[BootstrapAttendeeSnapshot],
    settings: SpeakerBootstrapSettings,
    model: str,
    caller: EvidenceCaller | None = None,
) -> BootstrapEvidence:
    """Call the evidence prompt in overlapping chunks and validate/deduplicate its citations."""
    if not targets or not raw.transcript.utterances:
        return BootstrapEvidence(claims=())
    if len(raw.utterance_ids) != len(raw.transcript.utterances):
        raise ValueError("Diarized bootstrap transcript IDs do not match its utterance count.")

    invoke = caller or _call_prompt
    accepted: dict[tuple[uuid.UUID, str, tuple[int, ...], tuple[int, ...]], BootstrapEvidenceClaim] = {}
    chunks = _chunk_bounds(len(raw.transcript.utterances), settings.evidence_chunk_utterances, settings.evidence_context_utterances)
    for start, end in chunks:
        utterances = tuple(
            _PromptUtterance(
                index=index,
                speaker_id=raw.transcript.utterances[index].speaker,
                text=raw.transcript.utterances[index].punctuated_text or raw.transcript.utterances[index].text,
            )
            for index in range(start, end)
        )
        response = await _with_retries(invoke, _PromptData(attendees=targets, utterances=utterances), model, settings)
        for claim in _validated_claims(response, raw, targets, range(start, end)):
            candidate_indices = tuple(source.original_index for source in claim.candidate_utterance_ids)
            evidence_indices = tuple(source.original_index for source in claim.evidence_utterance_ids)
            accepted[(claim.player_id, claim.diarized_speaker_id, candidate_indices, evidence_indices)] = claim
    return BootstrapEvidence(claims=tuple(accepted[key] for key in sorted(accepted, key=lambda key: str(key))))


async def _call_prompt(prompt: PromptName, data: object, model: str, response_model: type[BaseModel], timeout: float) -> str:
    return await call_llm_with_prompt(prompt, data, model=model, response_model=response_model, timeout=timeout)


async def _with_retries(
    caller: EvidenceCaller, data: _PromptData, model: str, settings: SpeakerBootstrapSettings
) -> BootstrapEvidenceResponse:
    error: Exception | None = None
    for _attempt in range(settings.evidence_max_attempts):
        try:
            response = await caller(
                PromptName.PROPOSE_BOOTSTRAP_EVIDENCE, data, model, BootstrapEvidenceResponse, float(settings.evidence_timeout)
            )
            return BootstrapEvidenceResponse.model_validate_json(response)
        except Exception as exc:
            error = exc
    assert error is not None
    raise RuntimeError("Bootstrap identity evidence could not be prepared.") from error


def _validated_claims(
    response: BootstrapEvidenceResponse,
    raw: DiarizedBootstrapTranscript,
    targets: Sequence[BootstrapAttendeeSnapshot],
    chunk_indices: range,
) -> tuple[BootstrapEvidenceClaim, ...]:
    valid_targets = {target.player_id for target in targets}
    valid_indices = set(chunk_indices)
    claims: list[BootstrapEvidenceClaim] = []
    for response_claim in response.claims:
        candidate_indices = tuple(dict.fromkeys(response_claim.candidate_utterance_indices))
        evidence_indices = tuple(dict.fromkeys(response_claim.evidence_utterance_indices))
        if (
            response_claim.player_id not in valid_targets
            or not candidate_indices
            or not evidence_indices
            or any(index not in valid_indices for index in (*candidate_indices, *evidence_indices))
            or any(raw.transcript.utterances[index].speaker != response_claim.diarized_speaker_id for index in candidate_indices)
        ):
            continue
        claims.append(
            BootstrapEvidenceClaim(
                player_id=response_claim.player_id,
                diarized_speaker_id=response_claim.diarized_speaker_id,
                candidate_utterance_ids=tuple(raw.utterance_ids[index] for index in candidate_indices),
                evidence_utterance_ids=tuple(raw.utterance_ids[index] for index in evidence_indices),
                explanation=response_claim.explanation.strip(),
            )
        )
    return tuple(claims)


def _chunk_bounds(total: int, chunk_size: int, context_size: int) -> tuple[tuple[int, int], ...]:
    bounds: list[tuple[int, int]] = []
    for core_start in range(0, total, chunk_size):
        core_end = min(total, core_start + chunk_size)
        bounds.append((max(0, core_start - context_size), min(total, core_end + context_size)))
    return tuple(bounds)
