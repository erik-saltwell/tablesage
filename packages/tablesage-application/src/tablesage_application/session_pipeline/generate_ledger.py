from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, Self

import widelog
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, model_validator

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
NonEmptyTextList = Annotated[list[NonEmptyText], Field(min_length=1)]

MAX_GENERATION_ATTEMPTS = 3
LEDGER_MARKDOWN_FILENAME = "ledger.md"

# The human-readable role name seeded for a campaign's GM (mirrors `attendee_editor.py`'s
# `_GAME_MASTER_LABEL` and `entities/sessions.py`'s equivalent translation of the
# `GAME_MASTER_ROLE` magic value -- there's no shared constant for this literal today, this
# module follows the same precedent). `source` is otherwise an unvalidated free-text field
# (see `generate_ledger.md`), so this match is a heuristic, not a guarantee.
_GAME_MASTER_LABEL = "Game Master"


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


class Question(_StrictModel):
    type: Literal["question"]
    asker: NonEmptyText = Field(description="The player asking, by name, not the in-fiction character or role.")
    question: NonEmptyText = Field(description="What was asked.")
    resolver: NonEmptyText | None = Field(description="The player who resolved it, by name, if resolved.")
    resolution: NonEmptyText | None = Field(description="The resolving answer, if resolved.")

    @model_validator(mode="after")
    def _resolver_and_resolution_together(self) -> Self:
        if (self.resolver is None) != (self.resolution is None):
            raise ValueError("Question.resolver and Question.resolution must both be set or both be absent.")
        return self


LedgerUtterance = Annotated[Narration | Action | Speech | Expression | Correction | Question, Field(discriminator="type")]


def _require_meaningful_content(preamble: Preamble | None, utterances: list[LedgerUtterance]) -> None:
    if preamble is None and not utterances:
        raise ValueError("Ledger must contain meaningful content in its preamble or regular utterances.")


class Attendee(_StrictModel):
    player_name: NonEmptyText
    roles: tuple[NonEmptyText, ...]


class Ledger(_StrictModel):
    version: Literal[3] = 3
    session_id: uuid.UUID
    session_name: NonEmptyText
    attendees: tuple[Attendee, ...] = ()
    preamble: Preamble | None
    utterances: list[LedgerUtterance]

    @model_validator(mode="after")
    def _require_content(self) -> Self:
        _require_meaningful_content(self.preamble, self.utterances)
        return self

    def save(self, path: Path) -> None:
        path.write_text(f"{self.model_dump_json(indent=2)}\n", encoding="utf-8")

    def to_markdown(self) -> str:
        """Render a faithful, human-readable view without changing or reinterpreting Ledger content."""
        lines = [f"# {self.session_name}", ""]
        if self.attendees:
            attendee_line = " · ".join(
                f"{attendee.player_name} ({', '.join(attendee.roles) if attendee.roles else 'No roles'})" for attendee in self.attendees
            )
            lines.append(f"**Attendees:** {attendee_line}")
        else:
            lines.append("_No attendees recorded._")

        if self.preamble is not None and self.preamble.recap is not None:
            lines.extend(["", "## Recap", ""])
            for index, event in enumerate(self.preamble.recap.events, start=1):
                lines.append(f"{index}. {event}")
            if self.preamble.recap.opening_situation is not None:
                lines.extend(["", f"**Opening:** {self.preamble.recap.opening_situation}"])

        if self.preamble is not None and self.preamble.character_introductions is not None:
            lines.extend(["", "## Characters", ""])
            for introduction in self.preamble.character_introductions:
                lines.append(f"- **{introduction.character}** — {introduction.description}")

        lines.extend(["", "## Session", ""])
        for index, utterance in enumerate(self.utterances, start=1):
            lines.append(_render_markdown_utterance(index, utterance))
            lines.append("")

        lines.extend(["---", "", f"*Session `{self.session_id}` · ledger format {self.version}*"])
        return "\n".join(lines).rstrip() + "\n"

    @classmethod
    def load(cls, path: Path) -> Ledger:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))


def _render_markdown_utterance(index: int, utterance: LedgerUtterance) -> str:
    if isinstance(utterance, Question):
        if utterance.resolver is None:
            return f"{index}. **? {utterance.asker}:** {utterance.question} → *unresolved*"
        return f"{index}. **? {utterance.asker}:** {utterance.question} **→ {utterance.resolver}:** {utterance.resolution}"

    if isinstance(utterance, Correction):
        return f"{index}. **⚠ Correction ({utterance.source}):** {utterance.revision}"

    if isinstance(utterance, Narration):
        attribution = "" if utterance.source == _GAME_MASTER_LABEL else f" *— {utterance.source}*"
        return f"{index}. {utterance.fact}{attribution}"

    if isinstance(utterance, Speech):
        return f"{index}. **{utterance.entity}:** {utterance.statement}"

    if isinstance(utterance, Action):
        return f"{index}. **{utterance.entity}** — {utterance.action}"

    return f"{index}. **{utterance.entity}** — *{utterance.sentiment}*"


class LedgerGenerationResponse(_StrictModel):
    scratchpad: str = Field(description="Brief generation planning notes; discarded by the application.")
    preamble: Preamble | None
    utterances: list[LedgerUtterance]

    @model_validator(mode="after")
    def _require_content(self) -> Self:
        _require_meaningful_content(self.preamble, self.utterances)
        return self


@dataclass(frozen=True)
class GlossaryPromptEntry:
    term: str
    description: str | None


@dataclass(frozen=True)
class LedgerPromptData:
    transcript: str
    known_roles: tuple[str, ...]
    attendees: tuple[Attendee, ...]
    glossary: tuple[GlossaryPromptEntry, ...]


@dataclass(frozen=True)
class _Candidate:
    response: LedgerGenerationResponse
    warning_count: int
    attempt: int


def can_generate_ledger(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename).is_file():
        return False, "Clean the transcript first."
    return True, None


def _introduction_warning_count(response: LedgerGenerationResponse, known_roles: frozenset[str]) -> int:
    warning_count = 0
    if response.preamble is not None and response.preamble.character_introductions is not None:
        warning_count += sum(introduction.character not in known_roles for introduction in response.preamble.character_introductions)
    return warning_count


def _attendee_warning_count(response: LedgerGenerationResponse, known_players: frozenset[str]) -> int:
    warning_count = 0
    for utterance in response.utterances:
        if not isinstance(utterance, Question):
            continue
        warning_count += utterance.asker not in known_players
        if utterance.resolver is not None:
            warning_count += utterance.resolver not in known_players
    return warning_count


async def generate_ledger(
    transcript: str,
    known_roles: Sequence[str],
    attendees: Sequence[Attendee],
    glossary: Sequence[GlossaryPromptEntry],
    model: str,
) -> LedgerGenerationResponse:
    """Generate the best structurally valid whole-session Ledger content in at most three attempts.

    Structurally invalid responses are unavailable as candidates. Unknown introduced characters
    and Question attendees are warnings: they trigger another attempt, but after the final attempt
    the parseable candidate with the fewest warnings is returned (earliest wins ties). Regular
    `source` values are intentionally unrestricted beyond the schema's non-empty-string rule.
    """
    normalized_roles = tuple(sorted({role.strip() for role in known_roles if role.strip()}))
    known_role_set = frozenset(normalized_roles)
    normalized_attendees = tuple(
        sorted(
            (
                Attendee(
                    player_name=attendee.player_name.strip(),
                    roles=tuple(sorted({role.strip() for role in attendee.roles if role.strip()})),
                )
                for attendee in attendees
            ),
            key=lambda attendee: attendee.player_name.casefold(),
        )
    )
    known_player_set = frozenset(attendee.player_name for attendee in normalized_attendees)
    prompt_data = LedgerPromptData(
        transcript=transcript, known_roles=normalized_roles, attendees=normalized_attendees, glossary=tuple(glossary)
    )
    candidates: list[_Candidate] = []
    last_error: Exception | None = None

    with widelog.wide_event(
        op="generate_ledger",
        model=model,
        known_role_count=len(normalized_roles),
        attendee_count=len(normalized_attendees),
        glossary_count=len(glossary),
    ) as log:
        for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
            log.set(attempt_count=attempt)
            raw = await call_llm_with_prompt(
                PromptName.GENERATE_LEDGER,
                prompt_data,
                model,
                response_model=LedgerGenerationResponse,
            )
            try:
                response = LedgerGenerationResponse.model_validate_json(raw)
            except ValidationError as exc:
                last_error = exc
                continue

            warning_count = _introduction_warning_count(response, known_role_set) + _attendee_warning_count(response, known_player_set)
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

        log.set(
            attempt_count=MAX_GENERATION_ATTEMPTS,
            failed=True,
            failure_kind="structural_validation",
            last_validation_error=str(last_error) if last_error else None,
        )
        raise ValueError(
            f"Ledger generation failed structural validation in all {MAX_GENERATION_ATTEMPTS} attempts. Last validation error: {last_error}"
        ) from last_error
