from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GlossaryProposal(_StrictModel):
    term: NonEmptyText
    description: str | None = None


class GlossaryExtractionResponse(_StrictModel):
    entries: list[GlossaryProposal]


@dataclass(frozen=True)
class AttendeePromptEntry:
    player_name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class GlossaryPromptEntry:
    term: str
    description: str | None


@dataclass(frozen=True)
class GlossaryExtractionPromptData:
    transcript: str
    attendees: Sequence[AttendeePromptEntry]
    glossary: Sequence[GlossaryPromptEntry]


@dataclass(frozen=True)
class GlossaryCommitResult:
    added_count: int
    skipped_duplicate_count: int


def can_extract_glossary(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename).is_file():
        return False, "Generate the Role Transcript first."
    return True, None


def normalize_term(term: str) -> str:
    return term.strip().casefold()


def filter_existing_terms(proposals: Sequence[GlossaryProposal], existing_terms: Sequence[str]) -> list[GlossaryProposal]:
    existing = {normalize_term(term) for term in existing_terms}
    return [proposal for proposal in proposals if normalize_term(proposal.term) not in existing]


async def extract_glossary(
    transcript: str,
    attendees: Sequence[AttendeePromptEntry],
    glossary: Sequence[GlossaryPromptEntry],
    model: str,
) -> list[GlossaryProposal]:
    raw = await call_llm_with_prompt(
        PromptName.EXTRACT_GLOSSARY,
        GlossaryExtractionPromptData(transcript=transcript, attendees=attendees, glossary=glossary),
        model,
        response_model=GlossaryExtractionResponse,
    )
    response = GlossaryExtractionResponse.model_validate_json(raw)
    return response.entries
