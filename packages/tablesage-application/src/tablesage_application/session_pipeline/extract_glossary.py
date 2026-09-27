from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints
from tablesage_tools.model import Transcript

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


class ExtractedGlossaryTerms(_StrictModel):
    """The Add Glossary Entries step's receipt: the reviewed entries it committed to the campaign glossary.

    The entries themselves live in the database (duplicates of existing terms are skipped there). The receipt
    lists what was decided rather than what was newly added, so re-committing an unchanged decision leaves it
    identical and Spellcheck Against Glossary current.
    """

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
    added: tuple[GlossaryProposal, ...] = ()


def can_extract_glossary(session_folder: Path) -> tuple[bool, str | None]:
    if not (session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename).is_file():
        return False, "Generate the Role Transcript first."
    return True, None


def render_transcript_text(transcript: Transcript) -> str:
    """Render an utterance transcript (e.g. the identified one) in the Role Transcript's `**Speaker** - text` form."""
    lines = []
    for utterance in transcript.utterances:
        text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
        lines.append(f"**{utterance.speaker}** - {text}")
    return "\n\n".join(lines) + "\n"


def legacy_receipt_path(session_folder: Path) -> Path:
    """Where the receipt lived before it became a processing-state section (legacy import only)."""
    return session_folder / ARTIFACTS[ArtifactName.EXTRACTED_GLOSSARY_TERMS].filename


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
