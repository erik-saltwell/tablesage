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
LEDGER_MARKDOWN_FILENAME = "ledger.md"

# The human-readable role name seeded for a campaign's GM (mirrors `attendee_editor.py`'s
# `_GAME_MASTER_LABEL` and `entities/sessions.py`'s equivalent translation of the
# `GAME_MASTER_ROLE` magic value -- there's no shared constant for this literal today, this
# module follows the same precedent). `source` is otherwise an unvalidated free-text field
# (see `generate_ledger.md`), so this match is a heuristic, not a guarantee.
_GAME_MASTER_LABEL = "Game Master"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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


class Attendee(_StrictModel):
    player_name: NonEmptyText
    roles: tuple[NonEmptyText, ...]


class Ledger(_StrictModel):
    version: Literal[4] = 4
    session_id: uuid.UUID
    session_name: NonEmptyText
    attendees: tuple[Attendee, ...] = ()
    starting_situation: NonEmptyText
    utterances: list[LedgerUtterance]

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

        lines.extend(["", "## Starting Situation", "", self.starting_situation, "", "## Session", ""])
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
    starting_situation: NonEmptyText = Field(description="A concise statement of the immediate situation at the beginning of this Session.")
    utterances: list[LedgerUtterance]


@dataclass(frozen=True)
class GlossaryPromptEntry:
    term: str
    description: str | None


@dataclass(frozen=True)
class LedgerPromptData:
    starting_context: str
    session_utterances: str
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
    if not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename).is_file():
        return False, "Section the transcript first."
    return True, None


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
    starting_context: Sequence[RoutedUtterance],
    session_utterances: Sequence[RoutedUtterance],
    known_roles: Sequence[str],
    attendees: Sequence[Attendee],
    glossary: Sequence[GlossaryPromptEntry],
    model: str,
) -> LedgerGenerationResponse:
    """Generate the best structurally valid current-session Ledger content in at most three attempts.

    Structurally invalid responses are unavailable as candidates. Unknown Question attendees are
    warnings: they trigger another attempt, but after the final attempt the parseable candidate
    with the fewest warnings is returned (earliest wins ties). Regular `source` values are
    intentionally unrestricted beyond the schema's non-empty-string rule.
    """
    normalized_roles = tuple(sorted({role.strip() for role in known_roles if role.strip()}))
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
        starting_context=json.dumps([utterance.model_dump() for utterance in starting_context], ensure_ascii=False, indent=2),
        session_utterances=json.dumps([utterance.model_dump() for utterance in session_utterances], ensure_ascii=False, indent=2),
        known_roles=normalized_roles,
        attendees=normalized_attendees,
        glossary=tuple(glossary),
    )
    candidates: list[_Candidate] = []
    last_error: Exception | None = None

    with widelog.wide_event(
        op="generate_ledger",
        model=model,
        known_role_count=len(normalized_roles),
        attendee_count=len(normalized_attendees),
        glossary_count=len(glossary),
        starting_context_utterance_count=len(starting_context),
        session_utterance_count=len(session_utterances),
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

            warning_count = _attendee_warning_count(response, known_player_set)
            candidate = _Candidate(response=response, warning_count=warning_count, attempt=attempt)
            candidates.append(candidate)
            if warning_count == 0:
                log.set(
                    attempt_count=attempt,
                    warning_count=0,
                    generated_utterance_count=len(response.utterances),
                    starting_situation_chars=len(response.starting_situation),
                    failed=False,
                )
                return response

        if candidates:
            selected = min(candidates, key=lambda candidate: (candidate.warning_count, candidate.attempt))
            log.set(
                attempt_count=MAX_GENERATION_ATTEMPTS,
                warning_count=selected.warning_count,
                selected_attempt=selected.attempt,
                generated_utterance_count=len(selected.response.utterances),
                starting_situation_chars=len(selected.response.starting_situation),
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
