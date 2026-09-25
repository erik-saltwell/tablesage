from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints
from tablesage_tools.model import Transcript

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName
from .atomic_files import atomic_write

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GlossaryProposal(_StrictModel):
    term: NonEmptyText
    description: str | None = None


class GlossaryExtractionResponse(_StrictModel):
    entries: list[GlossaryProposal]


class ExtractedGlossaryTerms(_StrictModel):
    """`extracted_glossary_terms.json`: Process Session's Extract Glossary Terms receipt.

    Lists the entries the step's last write added to the campaign glossary. The entries themselves live in
    the database; this file is the step's completion marker, which Spellcheck Against Glossary depends on.
    Session Detail's Extract Glossary command never writes it.
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


def receipt_path(session_folder: Path) -> Path:
    return session_folder / ARTIFACTS[ArtifactName.EXTRACTED_GLOSSARY_TERMS].filename


def save_receipt(session_folder: Path, added: Sequence[GlossaryProposal], *, saved_is_current: bool) -> bool:
    """Write the step's receipt; return whether it was written.

    A current receipt is left alone when nothing was added: staleness is modification-time based, so
    rewriting it would needlessly invalidate Spellcheck Against Glossary, the manual transcript review, and
    everything after them. A missing or stale receipt is always written, even when empty, so the step completes.
    """
    if saved_is_current and not added:
        return False
    atomic_write(receipt_path(session_folder), ExtractedGlossaryTerms(entries=list(added)).model_dump_json(indent=2).encode("utf-8"))
    return True


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
