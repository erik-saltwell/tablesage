from __future__ import annotations

from enum import StrEnum
from importlib.resources import files
from pathlib import Path

_RESOURCE_PACKAGE = __name__.rsplit(".", maxsplit=1)[0]


class PromptName(StrEnum):
    """Each member names a subdirectory of `_prompts/` holding a `system.md` + `template.j2` pair."""

    SUMMARIZE_SESSION = "summarize_session"
    GENERATE_LEDGER = "generate_ledger"
    GENERATE_SCENE_LOG = "generate_scene_log"
    GENERATE_TABLE_RECAP = "generate_table_recap"
    GENERATE_SPOKEN_TABLE_RECAP = "generate_spoken_table_recap"
    GENERATE_MATTER_PRESENT_MATTERS = "generate_matter_present_matters"
    GENERATE_MATTER_OBLIGATIONS = "generate_matter_obligations"
    GENERATE_MATTER_GOALS = "generate_matter_goals"
    GENERATE_MATTER_BREWING_TROUBLES = "generate_matter_brewing_troubles"
    GENERATE_MATTER_GOAL_IMPEDIMENTS = "generate_matter_goal_impediments"
    GENERATE_MATTER_OPPORTUNITIES = "generate_matter_opportunities"
    GENERATE_MATTER_MYSTERIES = "generate_matter_mysteries"
    GENERATE_MATTER_NEW_ASSETS = "generate_matter_new_assets"
    GENERATE_MATTER_REVELATIONS = "generate_matter_revelations"
    GENERATE_MATTER_DEVELOPMENTS = "generate_matter_developments"
    ISOLATE_NEW_SPEAKERS = "isolate_new_speakers"
    CLASSIFY_BACKCHANNELS = "classify_backchannels"
    EXTRACT_GLOSSARY = "extract_glossary"
    SUGGEST_SPELLING_CORRECTIONS = "suggest_spelling_corrections"
    SUGGEST_NAME_CORRECTIONS = "suggest_name_corrections"
    SECTION_TRANSCRIPT = "section_transcript"
    GENERATE_PLAYER_INTRODUCTIONS = "generate_player_introductions"
    GENERATE_RECAP_SUMMARY = "generate_recap_summary"
    PREVIOUSLY_ON_INGREDIENTS = "previously_on_ingredients"
    PREVIOUSLY_ON_SCOUT = "previously_on_scout"
    PREVIOUSLY_ON_EDITOR = "previously_on_editor"
    GENERATE_OPPORTUNITIES = "generate_opportunities"


def system_prompt_path(name: PromptName) -> Path:
    """Return the installed filesystem path used for prompt freshness checks."""
    return Path(__file__).parent / name.value / "system.md"


def read_system_prompt(name: PromptName) -> str:
    return files(_RESOURCE_PACKAGE).joinpath(name.value, "system.md").read_text("utf-8")


def read_prompt_template(name: PromptName) -> str:
    return files(_RESOURCE_PACKAGE).joinpath(name.value, "template.j2").read_text("utf-8")
