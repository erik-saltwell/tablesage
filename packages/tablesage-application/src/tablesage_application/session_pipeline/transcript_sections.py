from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, Self

import widelog
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, model_validator

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName
from .role_transcript import RoleTranscript, RoleTranscriptUtterance

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
MAX_GENERATION_ATTEMPTS = 3


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InclusiveUtteranceRange(_StrictModel):
    """An inclusive range of role-transcript utterance indices."""

    start_index: int = Field(ge=0)
    end_index: int = Field(ge=0)

    @model_validator(mode="after")
    def _require_ordered_indices(self) -> Self:
        if self.end_index < self.start_index:
            raise ValueError("end_index must be greater than or equal to start_index.")
        return self


class TranscriptSectionsGenerationResponse(_StrictModel):
    """Structured output requested from the transcript-sectioning LLM pass."""

    scratchpad: str
    recap_range: InclusiveUtteranceRange | None
    introduction_range: InclusiveUtteranceRange | None
    starting_context_range: InclusiveUtteranceRange | None
    session_start_index: int = Field(ge=0)


class TranscriptSections(_StrictModel):
    """Persisted routing decisions tied to the exact bytes of a role transcript."""

    version: Literal[1] = 1
    role_transcript_sha256: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
    recap_range: InclusiveUtteranceRange | None
    introduction_range: InclusiveUtteranceRange | None
    starting_context_range: InclusiveUtteranceRange | None
    session_start_index: int = Field(ge=0)

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")


class Attendee(_StrictModel):
    player_name: NonEmptyText
    roles: tuple[NonEmptyText, ...]


@dataclass(frozen=True)
class TranscriptSectionsPromptData:
    attendees: tuple[Attendee, ...]
    role_transcript: str


class RoutedUtterance(_StrictModel):
    speaker: NonEmptyText
    text: NonEmptyText


@dataclass(frozen=True)
class RoutedTranscript:
    """Transcript views routed to downstream generators, with indices removed."""

    recap: tuple[RoutedUtterance, ...]
    introductions: tuple[RoutedUtterance, ...]
    starting_context: tuple[RoutedUtterance, ...]
    session: tuple[RoutedUtterance, ...]


class TranscriptSectionsValidationError(ValueError):
    """A structurally valid section response that does not fit its transcript."""


def can_generate_transcript_sections(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename).is_file():
        return False, "Clean the transcript first."
    return True, None


def role_transcript_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_range(name: str, value: InclusiveUtteranceRange | None, utterance_count: int) -> None:
    if value is not None and value.end_index >= utterance_count:
        raise TranscriptSectionsValidationError(
            f"{name}.end_index {value.end_index} is outside a transcript with {utterance_count} utterances."
        )


def validate_generation_response(
    response: TranscriptSectionsGenerationResponse, utterance_count: int
) -> TranscriptSectionsGenerationResponse:
    if response.session_start_index > utterance_count:
        raise TranscriptSectionsValidationError(
            f"session_start_index {response.session_start_index} is outside a transcript with {utterance_count} utterances."
        )
    _validate_range("recap_range", response.recap_range, utterance_count)
    _validate_range("introduction_range", response.introduction_range, utterance_count)
    _validate_range("starting_context_range", response.starting_context_range, utterance_count)
    return response


async def generate_transcript_sections(
    role_transcript: RoleTranscript,
    attendees: Sequence[Attendee],
    model: str,
) -> TranscriptSectionsGenerationResponse:
    """Classify opening transcript sections, retrying invalid structured output up to three times."""
    normalized_attendees = tuple(
        sorted(
            (
                Attendee(
                    player_name=attendee.player_name,
                    roles=tuple(sorted(set(attendee.roles), key=str.casefold)),
                )
                for attendee in attendees
            ),
            key=lambda attendee: attendee.player_name.casefold(),
        )
    )
    prompt_data = TranscriptSectionsPromptData(
        attendees=normalized_attendees,
        role_transcript=role_transcript.model_dump_json(indent=2),
    )
    last_error: Exception | None = None

    with widelog.wide_event(
        op="generate_transcript_sections",
        model=model,
        attendee_count=len(normalized_attendees),
        utterance_count=len(role_transcript.utterances),
    ) as log:
        for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
            log.set(attempt_count=attempt)
            raw = await call_llm_with_prompt(
                PromptName.SECTION_TRANSCRIPT,
                prompt_data,
                model,
                response_model=TranscriptSectionsGenerationResponse,
            )
            try:
                response = TranscriptSectionsGenerationResponse.model_validate_json(raw)
                validate_generation_response(response, len(role_transcript.utterances))
            except (ValidationError, TranscriptSectionsValidationError) as exc:
                last_error = exc
                continue
            log.set(
                attempt_count=attempt,
                failed=False,
                recap_range=response.recap_range.model_dump() if response.recap_range is not None else None,
                introduction_range=response.introduction_range.model_dump() if response.introduction_range is not None else None,
                starting_context_range=(
                    response.starting_context_range.model_dump() if response.starting_context_range is not None else None
                ),
                session_start_index=response.session_start_index,
            )
            return response

        log.set(failed=True, failure_kind="structural_validation", last_validation_error=str(last_error))
        raise TranscriptSectionsValidationError(
            f"Transcript sectioning failed validation in all {MAX_GENERATION_ATTEMPTS} attempts. Last validation error: {last_error}"
        ) from last_error


def persist_transcript_sections(
    response: TranscriptSectionsGenerationResponse,
    role_transcript_path: Path,
    target: Path,
) -> TranscriptSections:
    """Atomically persist validated routing metadata for the exact role-transcript bytes."""
    role_transcript = RoleTranscript.load(role_transcript_path)
    validate_generation_response(response, len(role_transcript.utterances))
    sections = TranscriptSections(
        role_transcript_sha256=role_transcript_sha256(role_transcript_path),
        recap_range=response.recap_range,
        introduction_range=response.introduction_range,
        starting_context_range=response.starting_context_range,
        session_start_index=response.session_start_index,
    )
    temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
    try:
        sections.save(temporary)
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return sections


def load_current_transcript_sections(role_transcript_path: Path, sections_path: Path) -> TranscriptSections:
    sections = TranscriptSections.load(sections_path)
    actual_digest = role_transcript_sha256(role_transcript_path)
    if sections.role_transcript_sha256 != actual_digest:
        raise TranscriptSectionsValidationError("Transcript sections were generated from a different role transcript.")
    role_transcript = RoleTranscript.load(role_transcript_path)
    validate_generation_response(
        TranscriptSectionsGenerationResponse(
            scratchpad="",
            recap_range=sections.recap_range,
            introduction_range=sections.introduction_range,
            starting_context_range=sections.starting_context_range,
            session_start_index=sections.session_start_index,
        ),
        len(role_transcript.utterances),
    )
    return sections


def _without_indices(utterances: Sequence[RoleTranscriptUtterance]) -> tuple[RoutedUtterance, ...]:
    return tuple(RoutedUtterance(speaker=utterance.speaker, text=utterance.text) for utterance in utterances)


def _inclusive_slice(transcript: RoleTranscript, section_range: InclusiveUtteranceRange | None) -> tuple[RoutedUtterance, ...]:
    if section_range is None:
        return ()
    return _without_indices(transcript.utterances[section_range.start_index : section_range.end_index + 1])


def route_transcript(role_transcript: RoleTranscript, sections: TranscriptSections) -> RoutedTranscript:
    """Build index-free views for the three side outputs and session-only Ledger input."""
    validate_generation_response(
        TranscriptSectionsGenerationResponse(
            scratchpad="",
            recap_range=sections.recap_range,
            introduction_range=sections.introduction_range,
            starting_context_range=sections.starting_context_range,
            session_start_index=sections.session_start_index,
        ),
        len(role_transcript.utterances),
    )
    if sections.starting_context_range is None:
        raise TranscriptSectionsValidationError("starting_context_range is required before downstream generation can continue.")
    return RoutedTranscript(
        recap=_inclusive_slice(role_transcript, sections.recap_range),
        introductions=_inclusive_slice(role_transcript, sections.introduction_range),
        starting_context=_inclusive_slice(role_transcript, sections.starting_context_range),
        session=_without_indices(role_transcript.utterances[sections.session_start_index :]),
    )


def slice_introduction_transcript(role_transcript: RoleTranscript, sections: TranscriptSections) -> tuple[RoutedUtterance, ...] | None:
    """Select the Introduction Range without requiring other downstream routing fields."""
    validate_generation_response(
        TranscriptSectionsGenerationResponse(
            scratchpad="",
            recap_range=sections.recap_range,
            introduction_range=sections.introduction_range,
            starting_context_range=sections.starting_context_range,
            session_start_index=sections.session_start_index,
        ),
        len(role_transcript.utterances),
    )
    if sections.introduction_range is None:
        return None
    return _inclusive_slice(role_transcript, sections.introduction_range)
