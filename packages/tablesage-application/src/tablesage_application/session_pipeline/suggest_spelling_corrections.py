from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints
from tablesage_tools.model import Transcript

from ..llm import PromptName, call_llm_with_prompt
from .transcript_review import count_occurrences

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SpellingSuggestionProposal(_StrictModel):
    from_text: NonEmptyText
    to_text: NonEmptyText


class SpellingSuggestionsResponse(_StrictModel):
    suggestions: list[SpellingSuggestionProposal]


@dataclass(frozen=True)
class SuggestSpellingCorrectionsPromptData:
    """`template_data` for `PromptName.SUGGEST_SPELLING_CORRECTIONS` -- see `_prompts/suggest_spelling_corrections/template.j2`."""

    transcript: str
    attendees: Sequence[str]
    glossary: Sequence[str]


@dataclass(frozen=True)
class SpellingSuggestion:
    """One accepted `from`->`to` suggestion, ready for a review table row.

    `case_sensitive` always starts False here -- the LLM never decides this; it's a per-row
    default the user can flip in the review table, same shape as `FindReplaceResult` but with
    the opposite default (ASR mishearings this feature targets often differ only in case).
    `occurrence_count` is a snapshot at proposal time; the review table recomputes it live via
    `count_occurrences` if the user edits `from_text` or `case_sensitive`.
    """

    from_text: str
    to_text: str
    case_sensitive: bool
    occurrence_count: int


def _render_transcript(transcript: Transcript) -> str:
    lines = []
    for utterance in transcript.utterances:
        text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
        lines.append(f"{utterance.speaker}: {text}")
    return "\n".join(lines)


def filter_and_dedupe_suggestions(proposals: Sequence[SpellingSuggestionProposal], transcript: Transcript) -> list[SpellingSuggestion]:
    """Drop suggestions that can't do anything, then attach a live occurrence count.

    Three filters, in order: `from_text` must actually occur (case-insensitively) in the
    transcript -- a model-imprecision snippet that matches nothing is inert noise, not worth
    reviewing; `to_text` must differ from `from_text` (case-insensitively) -- a no-op; and
    duplicate `from_text` values keep only the first (an implementation-defined winner, not a
    merge -- rare enough that the surviving row's own Edit/Delete covers it).
    """
    seen_from: set[str] = set()
    suggestions: list[SpellingSuggestion] = []
    for proposal in proposals:
        from_text = proposal.from_text.strip()
        to_text = proposal.to_text.strip()
        if not from_text or from_text.casefold() == to_text.casefold():
            continue
        key = from_text.casefold()
        if key in seen_from:
            continue
        occurrence_count = count_occurrences(transcript, from_text, case_sensitive=False)
        if occurrence_count == 0:
            continue
        seen_from.add(key)
        suggestions.append(
            SpellingSuggestion(from_text=from_text, to_text=to_text, case_sensitive=False, occurrence_count=occurrence_count)
        )
    return suggestions


async def suggest_spelling_corrections(
    transcript: Transcript,
    glossary_terms: Sequence[str],
    attendee_names: Sequence[str],
    model: str,
) -> list[SpellingSuggestionProposal]:
    """Ask *model* for `from`/`to` spelling-correction suggestions across the whole *transcript*.

    One call for the entire transcript (not one per utterance) -- whole-transcript context lets
    the model disambiguate between similarly-sounding known terms in a way an isolated
    single-utterance call could not. Returns raw proposals; `filter_and_dedupe_suggestions` is a
    separate step so callers can filter without needing to re-run the LLM call.
    """
    raw = await call_llm_with_prompt(
        PromptName.SUGGEST_SPELLING_CORRECTIONS,
        SuggestSpellingCorrectionsPromptData(transcript=_render_transcript(transcript), attendees=attendee_names, glossary=glossary_terms),
        model,
        response_model=SpellingSuggestionsResponse,
    )
    return SpellingSuggestionsResponse.model_validate_json(raw).suggestions
