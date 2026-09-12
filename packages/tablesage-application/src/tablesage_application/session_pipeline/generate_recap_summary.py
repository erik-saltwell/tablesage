from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName
from .scene_breakdown import SceneBreakdown, load_current_scene_breakdown

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
class RecapSummaryPromptData:
    scene_breakdown: str
    attendees: Sequence[Attendee]
    glossary: Sequence[GlossaryPromptEntry]
    campaign_name: str
    session_date: str | None
    game_system: str | None


def can_generate_recap_summary(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.SCENE_BREAKDOWN].filename).is_file():
        return False, "Generate the Ledger and Scene Breakdown first."
    try:
        load_current_scene_breakdown(session_folder)
    except (OSError, ValueError) as exc:
        return False, f"Regenerate the Ledger and Scene Breakdown: {exc}"
    return True, None


def validate_recap_bullets(raw: str) -> str:
    """Validate the same flat-bullet contract used by production and optimization."""
    if not raw.strip():
        raise ValueError("The Recap Summary model returned an empty response.")
    if "```" in raw or any(re.fullmatch(r"- \S.*", line) is None for line in raw.splitlines() if line.strip()):
        raise ValueError("Recap Summary must contain only flat '- ' Markdown bullets, without headings or fences.")
    return raw.strip()


async def generate_recap_summary(
    scene_breakdown: str,
    attendees: Sequence[Attendee],
    glossary: Sequence[GlossaryPromptEntry],
    campaign_name: str,
    session_date: str | None,
    game_system: str | None,
    model: str,
) -> str:
    """Generate a reusable Markdown Recap section from the Scene Breakdown alone."""
    SceneBreakdown.model_validate_json(scene_breakdown)
    prompt_data = RecapSummaryPromptData(
        scene_breakdown=scene_breakdown,
        attendees=attendees,
        glossary=glossary,
        campaign_name=campaign_name,
        session_date=session_date,
        game_system=game_system,
    )
    last_error: ValueError | None = None
    for _ in range(MAX_GENERATION_ATTEMPTS):
        raw = await call_llm_with_prompt(PromptName.GENERATE_RECAP_SUMMARY, prompt_data, model)
        try:
            bullet_content = validate_recap_bullets(raw)
        except ValueError as exc:
            last_error = exc
            continue
        return f"## Recap\n\n{bullet_content}\n"
    raise ValueError(f"Recap Summary failed validation in all {MAX_GENERATION_ATTEMPTS} attempts: {last_error}") from last_error


def persist_recap_summary(recap: str, target: Path) -> None:
    """Atomically replace the persisted Recap Summary."""
    temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
    try:
        temporary.write_text(recap, encoding="utf-8")
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
