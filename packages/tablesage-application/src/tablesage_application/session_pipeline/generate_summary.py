from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..llm import PromptName, call_llm_with_prompt


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
    raw = await call_llm_with_prompt(
        PromptName.SUMMARIZE_SESSION,
        SummaryPromptData(
            ledger=ledger,
            attendees=attendees,
            glossary=glossary,
            campaign_name=campaign_name,
            session_date=session_date,
            game_system=game_system,
        ),
        model,
    )
    summary = raw.strip()
    if not summary:
        raise ValueError("The summary model returned an empty response.")
    return f"{summary}\n"
