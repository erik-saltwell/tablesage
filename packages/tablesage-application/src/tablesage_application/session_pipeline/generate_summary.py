from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

import widelog

from ..llm import PromptName, call_llm_with_prompt

RECAP_MARKER = "<!-- RECAP -->"
PLAYER_INTRODUCTIONS_MARKER = "<!-- PLAYER_INTRODUCTIONS -->"
MAX_GENERATION_ATTEMPTS = 3


@dataclass(frozen=True)
class GlossaryPromptEntry:
    term: str
    description: str | None


@dataclass(frozen=True)
class Attendee:
    player_name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class SummaryPromptData:
    ledger: str
    attendees: Sequence[Attendee]
    glossary: Sequence[GlossaryPromptEntry]
    campaign_name: str
    session_date: str | None
    game_system: str | None


class SummaryValidationError(ValueError):
    """The model response does not contain the required composition markers."""


class SummaryCompositionError(ValueError):
    """Validated Summary content could not be composed with its sidecars."""


def validate_summary_markers(summary: str) -> str:
    """Return stripped Markdown when both markers occur exactly once in the required order."""
    candidate = summary.strip()
    if not candidate:
        raise SummaryValidationError("The summary model returned an empty response.")
    recap_count = candidate.count(RECAP_MARKER)
    introductions_count = candidate.count(PLAYER_INTRODUCTIONS_MARKER)
    if recap_count != 1 or introductions_count != 1:
        raise SummaryValidationError(
            "The summary must contain each composition marker exactly once "
            f"({RECAP_MARKER}: {recap_count}, {PLAYER_INTRODUCTIONS_MARKER}: {introductions_count})."
        )
    if candidate.index(RECAP_MARKER) > candidate.index(PLAYER_INTRODUCTIONS_MARKER):
        raise SummaryValidationError("The Recap marker must precede the Player Introductions marker.")
    return candidate


def _normalize_markdown(markdown: str) -> str:
    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n").strip()
    normalized = re.sub(r"\n(?:[ \t]*\n){2,}", "\n\n", normalized)
    return f"{normalized}\n"


def compose_summary(summary: str, recap_summary: str | None, player_introductions: str) -> str:
    """Replace validated markers with sidecars and normalize only surrounding whitespace."""
    candidate = validate_summary_markers(summary)
    recap = recap_summary.strip() if recap_summary is not None else ""
    if recap_summary is not None and not recap:
        raise SummaryCompositionError("The Recap Summary artifact is empty.")
    for marker in (RECAP_MARKER, PLAYER_INTRODUCTIONS_MARKER):
        if marker in recap or marker in player_introductions:
            raise SummaryCompositionError("A composition sidecar contains a reserved Summary marker.")
    composed = candidate.replace(RECAP_MARKER, recap).replace(PLAYER_INTRODUCTIONS_MARKER, player_introductions.strip())
    return _normalize_markdown(composed)


async def generate_summary(
    ledger: str,
    attendees: Sequence[Attendee],
    glossary: Sequence[GlossaryPromptEntry],
    campaign_name: str,
    session_date: str | None,
    game_system: str | None,
    model: str,
) -> str:
    """Generate normalized Markdown from source-agnostic summary prompt data.

    `ledger` is the session's canonical Ledger, serialized as JSON text -- this module reads it
    as an opaque string and does not depend on the Ledger's Pydantic schema. `session_date` and
    `game_system` are already formatted as strings (or `None`) by the caller.
    """
    prompt_data = SummaryPromptData(
        ledger=ledger,
        attendees=attendees,
        glossary=glossary,
        campaign_name=campaign_name,
        session_date=session_date,
        game_system=game_system,
    )
    last_error: SummaryValidationError | None = None

    with widelog.wide_event(op="generate_summary_template", model=model) as log:
        for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
            log.set(attempt_count=attempt)
            raw = await call_llm_with_prompt(PromptName.SUMMARIZE_SESSION, prompt_data, model)
            try:
                summary = validate_summary_markers(raw)
            except SummaryValidationError as exc:
                last_error = exc
                continue
            log.set(attempt_count=attempt, summary_template_chars=len(summary), failed=False)
            return f"{summary}\n"

        log.set(failed=True, failure_kind="validation", last_validation_error=str(last_error))
        raise SummaryValidationError(
            f"Summary generation failed marker validation in all {MAX_GENERATION_ATTEMPTS} attempts. Last validation error: {last_error}"
        ) from last_error
