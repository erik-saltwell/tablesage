from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, Self

import widelog
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
NonEmptyTextList = Annotated[list[NonEmptyText], Field(min_length=1)]

MAX_GENERATION_ATTEMPTS = 3


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Recap(_StrictModel):
    events: NonEmptyTextList = Field(description="Prior campaign events in the order the transcript describes them.")
    opening_situation: NonEmptyText | None = Field(description="The situation in which the new session begins, when stated.")


class CharacterIntroduction(_StrictModel):
    character: NonEmptyText = Field(description="The introduced character's role name.")
    description: NonEmptyText = Field(description="A condensed description of the character's explicit introduction.")


class Preamble(_StrictModel):
    recap: Recap | None = Field(description="An explicitly framed recap of prior campaign events.")
    character_introductions: Annotated[list[CharacterIntroduction], Field(min_length=1)] | None = Field(
        description="Explicit character introductions in first-introduction order."
    )

    @model_validator(mode="after")
    def _require_content_and_unique_characters(self) -> Self:
        if self.recap is None and self.character_introductions is None:
            raise ValueError("Preamble must contain a recap, character introductions, or both.")
        if self.character_introductions is not None:
            normalized = [introduction.character.casefold() for introduction in self.character_introductions]
            if len(normalized) != len(set(normalized)):
                raise ValueError("Preamble must contain one introduction per character.")
        return self


class _LedgerUtterance(_StrictModel):
    source: NonEmptyText = Field(description="The role or character associated with this move.")


class Narration(_LedgerUtterance):
    type: Literal["narration"]
    fact: NonEmptyText = Field(description="Something established as true about the game state.")


class Action(_LedgerUtterance):
    type: Literal["action"]
    entity: NonEmptyText = Field(description="The entity acting in the game world.")
    action: NonEmptyText = Field(description="What the entity does.")


class Speech(_LedgerUtterance):
    type: Literal["speech"]
    entity: NonEmptyText = Field(description="The entity speaking in the game world.")
    statement: NonEmptyText = Field(description="What the entity says, verbatim or paraphrased.")


class Expression(_LedgerUtterance):
    type: Literal["expression"]
    entity: NonEmptyText = Field(description="The entity whose inner life is expressed.")
    sentiment: NonEmptyText = Field(description="What the entity feels or realizes.")


class Correction(_LedgerUtterance):
    type: Literal["correction"]
    revision: NonEmptyText = Field(description="The revised canonical state, including what prior understanding it changes.")


LedgerUtterance = Annotated[Narration | Action | Speech | Expression | Correction, Field(discriminator="type")]


def _require_meaningful_content(preamble: Preamble | None, utterances: list[LedgerUtterance]) -> None:
    if preamble is None and not utterances:
        raise ValueError("Ledger must contain meaningful content in its preamble or regular utterances.")


class Ledger(_StrictModel):
    version: Literal[3] = 3
    session_id: uuid.UUID
    session_name: NonEmptyText
    preamble: Preamble | None
    utterances: list[LedgerUtterance]

    @model_validator(mode="after")
    def _require_content(self) -> Self:
        _require_meaningful_content(self.preamble, self.utterances)
        return self

    def save(self, path: Path) -> None:
        path.write_text(f"{self.model_dump_json(indent=2)}\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Ledger:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))


class LedgerGenerationResponse(_StrictModel):
    scratchpad: str = Field(description="Brief generation planning notes; discarded by the application.")
    preamble: Preamble | None
    utterances: list[LedgerUtterance]

    @model_validator(mode="after")
    def _require_content(self) -> Self:
        _require_meaningful_content(self.preamble, self.utterances)
        return self


@dataclass(frozen=True)
class LedgerPromptData:
    transcript: str
    known_roles: tuple[str, ...]


@dataclass(frozen=True)
class _Candidate:
    response: LedgerGenerationResponse
    warning_count: int
    attempt: int


def can_generate_ledger(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).is_file():
        return False, "Transcribe the session first."
    return True, None


def _role_warning_count(response: LedgerGenerationResponse, known_roles: frozenset[str]) -> int:
    warning_count = sum(utterance.source not in known_roles for utterance in response.utterances)
    if response.preamble is not None and response.preamble.character_introductions is not None:
        warning_count += sum(introduction.character not in known_roles for introduction in response.preamble.character_introductions)
    return warning_count


async def generate_ledger(transcript: str, known_roles: Sequence[str], model: str) -> LedgerGenerationResponse:
    """Generate the best structurally valid whole-session Ledger content in at most three attempts.

    Structurally invalid responses are unavailable as candidates. Unknown regular sources and
    introduced characters are warnings: they trigger another attempt, but after the final attempt
    the parseable candidate with the fewest warnings is returned (earliest wins ties).
    """
    normalized_roles = tuple(sorted({role.strip() for role in known_roles if role.strip()}))
    known_role_set = frozenset(normalized_roles)
    prompt_data = LedgerPromptData(transcript=transcript, known_roles=normalized_roles)
    candidates: list[_Candidate] = []
    last_error: Exception | None = None

    with widelog.wide_event(op="generate_ledger", known_role_count=len(normalized_roles)) as log:
        for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
            try:
                raw = await call_llm_with_prompt(
                    PromptName.GENERATE_LEDGER,
                    prompt_data,
                    model,
                    response_model=LedgerGenerationResponse,
                )
                response = LedgerGenerationResponse.model_validate_json(raw)
            except Exception as exc:
                last_error = exc
                continue

            warning_count = _role_warning_count(response, known_role_set)
            candidate = _Candidate(response=response, warning_count=warning_count, attempt=attempt)
            candidates.append(candidate)
            if warning_count == 0:
                log.set(attempt_count=attempt, warning_count=0, failed=False)
                return response

        if candidates:
            selected = min(candidates, key=lambda candidate: (candidate.warning_count, candidate.attempt))
            log.set(
                attempt_count=MAX_GENERATION_ATTEMPTS,
                warning_count=selected.warning_count,
                selected_attempt=selected.attempt,
                failed=False,
            )
            return selected.response

        log.set(attempt_count=MAX_GENERATION_ATTEMPTS, failed=True, error=str(last_error) if last_error else None)
        raise ValueError(
            f"Ledger generation produced no structurally valid response in {MAX_GENERATION_ATTEMPTS} attempts."
        ) from last_error
