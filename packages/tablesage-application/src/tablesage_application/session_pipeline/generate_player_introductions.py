from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, Self

import widelog
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, model_validator

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName
from .transcript_sections import RoutedUtterance

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
MAX_GENERATION_ATTEMPTS = 3
_GAME_MASTER_LABEL = "Game Master"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PlayerIntroduction(_StrictModel):
    character: NonEmptyText
    description: NonEmptyText


def _require_unique_characters(introductions: Sequence[PlayerIntroduction]) -> None:
    normalized = [introduction.character.casefold() for introduction in introductions]
    if len(normalized) != len(set(normalized)):
        raise ValueError("Player Introductions must contain each character at most once.")


class PlayerIntroductionsGenerationResponse(_StrictModel):
    scratchpad: str = Field(description="Brief extraction notes; discarded by the application.")
    introductions: list[PlayerIntroduction]

    @model_validator(mode="after")
    def _unique_characters(self) -> Self:
        _require_unique_characters(self.introductions)
        return self


class PlayerIntroductions(_StrictModel):
    version: Literal[1] = 1
    session_id: uuid.UUID
    introductions: list[PlayerIntroduction]

    @model_validator(mode="after")
    def _unique_characters(self) -> Self:
        _require_unique_characters(self.introductions)
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")

    def to_markdown(self) -> str:
        if not self.introductions:
            return ""
        lines = ["## Player Characters", ""]
        lines.extend(f"- **{introduction.character}** — {introduction.description}" for introduction in self.introductions)
        return "\n".join(lines) + "\n"


class Attendee(_StrictModel):
    player_name: NonEmptyText
    roles: tuple[NonEmptyText, ...]


class GlossaryPromptEntry(_StrictModel):
    term: NonEmptyText
    description: NonEmptyText | None


@dataclass(frozen=True)
class PlayerIntroductionsPromptData:
    campaign_name: str
    game_system: str | None
    session_date: str | None
    attendees: tuple[Attendee, ...]
    glossary: tuple[GlossaryPromptEntry, ...]
    introduction_transcript: str


class PlayerIntroductionsValidationError(ValueError):
    """A structurally valid response containing an ineligible character."""


def can_generate_player_introductions(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename).is_file():
        return False, "Clean the transcript first."
    if not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename).is_file():
        return False, "Section the transcript first."
    return True, None


def _eligible_roles(attendees: Sequence[Attendee]) -> frozenset[str]:
    player_names = {attendee.player_name for attendee in attendees}
    return frozenset(
        role
        for attendee in attendees
        for role in attendee.roles
        if role.casefold() != _GAME_MASTER_LABEL.casefold() and role not in player_names
    )


def _validate_characters(introductions: Sequence[PlayerIntroduction], eligible_roles: frozenset[str]) -> None:
    invalid = [introduction.character for introduction in introductions if introduction.character not in eligible_roles]
    if invalid:
        raise PlayerIntroductionsValidationError(f"Player Introductions contained ineligible characters: {', '.join(invalid)}.")


def validate_player_introductions(introductions: PlayerIntroductions, attendees: Sequence[Attendee]) -> None:
    """Validate a persisted sidecar against the Session's current attendee-role mapping."""
    _validate_characters(introductions.introductions, _eligible_roles(attendees))


async def generate_player_introductions(
    introduction_transcript: Sequence[RoutedUtterance] | None,
    attendees: Sequence[Attendee],
    glossary: Sequence[GlossaryPromptEntry],
    campaign_name: str,
    session_date: str | None,
    game_system: str | None,
    model: str,
) -> PlayerIntroductionsGenerationResponse:
    """Generate validated player-character introductions, or skip the LLM for a null range."""
    if introduction_transcript is None:
        return PlayerIntroductionsGenerationResponse(scratchpad="", introductions=[])

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
    normalized_glossary = tuple(sorted(glossary, key=lambda entry: entry.term.casefold()))
    eligible_roles = _eligible_roles(normalized_attendees)
    prompt_data = PlayerIntroductionsPromptData(
        campaign_name=campaign_name,
        game_system=game_system,
        session_date=session_date,
        attendees=normalized_attendees,
        glossary=normalized_glossary,
        introduction_transcript=json.dumps([utterance.model_dump() for utterance in introduction_transcript], ensure_ascii=False, indent=2),
    )
    last_error: Exception | None = None

    with widelog.wide_event(
        op="generate_player_introductions",
        model=model,
        attendee_count=len(normalized_attendees),
        eligible_role_count=len(eligible_roles),
        introduction_utterance_count=len(introduction_transcript),
    ) as log:
        for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
            log.set(attempt_count=attempt)
            raw = await call_llm_with_prompt(
                PromptName.GENERATE_PLAYER_INTRODUCTIONS,
                prompt_data,
                model,
                response_model=PlayerIntroductionsGenerationResponse,
            )
            try:
                response = PlayerIntroductionsGenerationResponse.model_validate_json(raw)
                _validate_characters(response.introductions, eligible_roles)
            except (ValidationError, PlayerIntroductionsValidationError) as exc:
                last_error = exc
                continue
            log.set(attempt_count=attempt, introduction_count=len(response.introductions), failed=False)
            return response

        log.set(failed=True, failure_kind="validation", last_validation_error=str(last_error))
        raise PlayerIntroductionsValidationError(
            f"Player Introductions generation failed validation in all {MAX_GENERATION_ATTEMPTS} attempts. "
            f"Last validation error: {last_error}"
        ) from last_error


def persist_player_introductions(
    response: PlayerIntroductionsGenerationResponse,
    session_id: uuid.UUID,
    target: Path,
) -> PlayerIntroductions:
    result = PlayerIntroductions(session_id=session_id, introductions=response.introductions)
    temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
    try:
        result.save(temporary)
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return result
