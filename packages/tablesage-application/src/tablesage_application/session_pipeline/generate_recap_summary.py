from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName


@dataclass(frozen=True)
class GlossaryPromptEntry:
    term: str
    description: str | None


@dataclass(frozen=True)
class Attendee:
    player_name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class RecapSummaryPromptData:
    ledger: str
    attendees: Sequence[Attendee]
    glossary: Sequence[GlossaryPromptEntry]
    campaign_name: str
    session_date: str | None
    game_system: str | None


def can_generate_recap_summary(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.LEDGER].filename).is_file():
        return False, "Generate the Ledger first."
    return True, None


async def generate_recap_summary(
    ledger: str,
    attendees: Sequence[Attendee],
    glossary: Sequence[GlossaryPromptEntry],
    campaign_name: str,
    session_date: str | None,
    game_system: str | None,
    model: str,
) -> str:
    """Generate a reusable Markdown Recap section from a canonical Ledger v4."""
    raw = await call_llm_with_prompt(
        PromptName.GENERATE_RECAP_SUMMARY,
        RecapSummaryPromptData(
            ledger=ledger,
            attendees=attendees,
            glossary=glossary,
            campaign_name=campaign_name,
            session_date=session_date,
            game_system=game_system,
        ),
        model,
    )
    bullet_content = raw.strip()
    if not bullet_content:
        raise ValueError("The Recap Summary model returned an empty response.")
    return f"## Recap\n\n{bullet_content}\n"


def persist_recap_summary(recap: str, target: Path) -> None:
    """Atomically replace the persisted Recap Summary."""
    temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
    try:
        temporary.write_text(recap, encoding="utf-8")
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
