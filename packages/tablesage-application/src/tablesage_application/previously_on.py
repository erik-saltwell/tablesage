"""Ephemeral campaign recall and external Markdown export, independent of Session artifacts."""

from __future__ import annotations

import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .llm import PromptName, call_llm_with_prompt
from .session_pipeline.scene_breakdown import Scene, SceneBreakdown

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PromptData(Record):
    payload: str


class SceneRef(Record):
    session_id: uuid.UUID
    scene_index: int = Field(ge=0, strict=True, description="Zero-based index in this Session's scenes array.")


class CampaignSession(Record):
    sequence_number: int
    breakdown: SceneBreakdown


class GlossaryEntry(Record):
    term: str
    description: str | None


class CampaignHistory(Record):
    campaign_name: str
    sessions: tuple[CampaignSession, ...]
    glossary: tuple[GlossaryEntry, ...]

    @property
    def starting_situation(self) -> str:
        return self.sessions[-1].breakdown.ending_situation

    @property
    def suggested_filename(self) -> str:
        sequence = max(session.sequence_number for session in self.sessions) + 1
        return f"{self.campaign_name}-{sequence:03d}-previously-on.md"

    def scene_catalog(self) -> dict[SceneRef, Scene]:
        return {
            SceneRef(session_id=session.breakdown.session_id, scene_index=index): scene
            for session in self.sessions
            for index, scene in enumerate(session.breakdown.scenes)
        }


class Ingredient(Record):
    label: Text
    current_state: Text
    sources: tuple[SceneRef, ...] = Field(min_length=1)


class Ingredients(Record):
    people_and_factions: tuple[Ingredient, ...] = Field(max_length=5)
    threads_and_commitments: tuple[Ingredient, ...] = Field(max_length=5)
    active_pressures: tuple[Ingredient, ...] = Field(max_length=5)
    places_and_objects: tuple[Ingredient, ...] = Field(max_length=5)

    def sections(self) -> tuple[tuple[str, tuple[Ingredient, ...]], ...]:
        return (
            ("People & Factions", self.people_and_factions),
            ("Threads & Commitments", self.threads_and_commitments),
            ("Active Pressures", self.active_pressures),
            ("Places & Objects", self.places_and_objects),
        )


class Recommendation(Record):
    source: SceneRef
    rationale: Text


class ScoutResult(Record):
    recommendations: tuple[Recommendation, ...]


class ScoutInput(Record):
    history: CampaignHistory
    starting_situation: str
    selected_ingredients: tuple[Ingredient, ...]
    upcoming_notes: str


class EditorInput(Record):
    """Deliberately cannot carry future notes, rationales, or unselected history."""

    selected_scenes: tuple[Scene, ...]
    starting_situation: str
    glossary: tuple[GlossaryEntry, ...]


def validate_sources(history: CampaignHistory, sources: tuple[SceneRef, ...]) -> None:
    catalog = history.scene_catalog()
    for source in sources:
        if source not in catalog:
            raise ValueError(f"Unknown Scene reference: Session {source.session_id}, Scene {source.scene_index + 1}.")


async def generate_ingredients(history: CampaignHistory, model: str, timeout: float) -> Ingredients:
    raw = await call_llm_with_prompt(
        PromptName.PREVIOUSLY_ON_INGREDIENTS,
        PromptData(payload=history.model_dump_json()),
        model,
        response_model=Ingredients,
        timeout=timeout,
    )
    result = Ingredients.model_validate_json(raw)
    validate_sources(history, tuple(source for _, items in result.sections() for item in items for source in item.sources))
    return result


async def scout_scenes(data: ScoutInput, model: str, timeout: float) -> ScoutResult:
    if not data.upcoming_notes.strip() and not data.selected_ingredients:
        raise ValueError("Add upcoming-session notes or select at least one ingredient.")
    validate_sources(data.history, tuple(source for item in data.selected_ingredients for source in item.sources))
    raw = await call_llm_with_prompt(
        PromptName.PREVIOUSLY_ON_SCOUT, PromptData(payload=data.model_dump_json()), model, response_model=ScoutResult, timeout=timeout
    )
    result = ScoutResult.model_validate_json(raw)
    sources = tuple(item.source for item in result.recommendations)
    validate_sources(data.history, sources)
    if len(set(sources)) != len(sources):
        raise ValueError("The scout returned duplicate Scene references. Please retry.")
    return result


def editor_input(history: CampaignHistory, selected: frozenset[SceneRef], starting_situation: str) -> EditorInput:
    if not selected:
        raise ValueError("Select at least one Scene before exporting.")
    validate_sources(history, tuple(selected))
    return EditorInput(
        selected_scenes=tuple(scene for ref, scene in history.scene_catalog().items() if ref in selected),
        starting_situation=starting_situation,
        glossary=history.glossary,
    )


async def write_recap(data: EditorInput, destination: Path, model: str, timeout: float, *, overwrite: bool = False) -> None:
    if destination.exists() and not overwrite:
        raise FileExistsError("Confirm replacement of the existing destination before generating the recap.")
    # The model owns the whole document: preserve even empty or malformed output verbatim.
    markdown = await call_llm_with_prompt(
        PromptName.PREVIOUSLY_ON_EDITOR, PromptData(payload=data.model_dump_json()), model, timeout=timeout
    )
    with TemporaryDirectory(prefix=".previously-on-", dir=destination.parent) as staging:
        temporary = Path(staging) / "recap.md"
        temporary.write_text(markdown, encoding="utf-8")
        if destination.exists() and not overwrite:
            raise FileExistsError("The destination appeared during generation. Confirm replacement before retrying.")
        temporary.replace(destination)
