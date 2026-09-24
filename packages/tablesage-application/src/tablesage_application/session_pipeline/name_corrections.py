"""Process Session's Review Name Corrections step: fix misheard player and character names.

The LLM proposes `from`/`to` corrections over the cleaned transcript against every attendee's
player name and character names; the user reviews them, and the approved ones are applied to
the cleaned transcript to write `name_corrected_transcript.json` -- the base transcript for every
later step. It runs before Isolate New Speakers because that step finds new players' utterances
largely from how people address each other, and a misspelled name hides that evidence.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import widelog
from pydantic import BaseModel, ConfigDict, create_model
from tablesage_tools.model import Transcript

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName
from .suggest_spelling_corrections import (
    Correction,
    SpellingSuggestion,
    render_transcript,
    save_corrected_transcript,
)
from .transcript_review import count_occurrences

# A correction replaces a misheard name, so a `from_text` longer than this has swallowed neighbouring words.
MAX_FROM_TEXT_WORDS = 3

# Words of a name that are titles or joiners, not names: "Sir" in "Sir Phidipaldi" is never a replacement target.
_NON_NAME_WORDS = frozenset({"sir", "dame", "lady", "lord", "dr", "mr", "mrs", "ms", "miss", "the", "of", "and", "von", "van", "de", "la"})


class _ProposalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    from_text: str
    to_text: str


class NameCorrectionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    suggestions: list[_ProposalResponse]


@dataclass(frozen=True)
class NamedPlayer:
    """One attendee as the prompt sees them: the player's own name and their characters' names."""

    player_name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class SuggestNameCorrectionsPromptData:
    """`template_data` for `PromptName.SUGGEST_NAME_CORRECTIONS` -- see `_prompts/suggest_name_corrections/template.j2`."""

    transcript: str
    players: Sequence[NamedPlayer]
    # Every spelling a correction may produce -- see `allowed_name_forms`.
    allowed_forms: Sequence[str]


def source_path(session_folder: Path) -> Path:
    return session_folder / ARTIFACTS[ArtifactName.CLEANED_TRANSCRIPT].filename


def output_path(session_folder: Path) -> Path:
    return session_folder / ARTIFACTS[ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename


def load_source(session_folder: Path) -> Transcript:
    """The cleaned transcript. Corrections always start from it, never from an earlier corrected copy."""
    return Transcript.load(source_path(session_folder))


def _name_words(name: str) -> list[str]:
    """The words of `name` that are names in their own right: not titles, joiners or very short."""
    words = (word.strip(".,'\"") for word in name.split())
    return [word for word in words if len(word) >= 3 and word.casefold() not in _NON_NAME_WORDS]


def allowed_name_forms(players: Sequence[NamedPlayer]) -> list[str]:
    """Every spelling a name correction may produce, in the listed spelling.

    For each player's name and each of their characters' names: the whole name, then each of its name words.
    People say "Eric" or "Fipaldi", not the whole name, so a correction must be able to replace only the part
    that was said -- otherwise fixing "Fipaldi" in "Sir Fipaldi" would insert "Sir Phidipaldi" and double the title.
    """
    forms: dict[str, str] = {}
    for player in players:
        for name in (player.player_name, *player.roles):
            candidates = [name.strip()]
            if len(name.split()) > 1:
                candidates.extend(_name_words(name))
            for form in candidates:
                if form:
                    forms.setdefault(form.casefold(), form)
    return list(forms.values())


def _constrained_response_model(forms: Sequence[str]) -> type[NameCorrectionsResponse]:
    """`NameCorrectionsResponse` whose schema only admits `forms` as a `to_text`."""
    form_type = Literal[tuple(forms)]  # ty: ignore[invalid-type-form]
    proposal = create_model("NameCorrection", __base__=_ProposalResponse, to_text=(form_type, ...))
    return create_model(
        "NameCorrectionsResponse",
        __base__=NameCorrectionsResponse,
        suggestions=(list[proposal], ...),  # ty: ignore[invalid-type-form]
    )


def _tokens(text: str) -> set[str]:
    return {token.casefold() for token in re.findall(r"[\w']+", text)}


def filter_name_suggestions(
    proposals: Sequence[_ProposalResponse], transcript: Transcript, forms: Sequence[str]
) -> tuple[list[SpellingSuggestion], Counter[str]]:
    """Keep the proposals that can safely be applied as whole-word find/replace; count each reason for dropping one.

    A proposal is dropped when it is a no-op, its `to_text` isn't an allowed form, its `from_text` is longer than
    `MAX_FROM_TEXT_WORDS` words (it has swallowed neighbouring words), it would overwrite a correctly spelled name
    (`from_text` holds a listed name word that `to_text` doesn't), it repeats an earlier `from_text`, or it matches
    no whole word of the transcript.
    """
    allowed = set(forms)
    name_words = {word.casefold() for form in forms for word in _name_words(form)}
    dropped: Counter[str] = Counter()
    seen: set[str] = set()
    suggestions: list[SpellingSuggestion] = []
    for proposal in proposals:
        from_text, to_text = proposal.from_text.strip(), proposal.to_text.strip()
        if not from_text or from_text.casefold() == to_text.casefold():
            dropped["no_op"] += 1
        elif to_text not in allowed:
            dropped["to_text_not_a_listed_name"] += 1
        elif len(from_text.split()) > MAX_FROM_TEXT_WORDS:
            dropped["from_text_too_long"] += 1
        elif (_tokens(from_text) & name_words) - _tokens(to_text):
            dropped["would_overwrite_a_listed_name"] += 1
        elif from_text.casefold() in seen:
            dropped["duplicate"] += 1
        else:
            occurrences = count_occurrences(transcript, from_text, case_sensitive=False, whole_words=True)
            if occurrences == 0:
                dropped["not_in_transcript"] += 1
                continue
            seen.add(from_text.casefold())
            suggestions.append(SpellingSuggestion(from_text=from_text, to_text=to_text, case_sensitive=False, occurrence_count=occurrences))
    return suggestions, dropped


async def suggest_name_corrections(
    transcript: Transcript, players: Sequence[NamedPlayer], model: str, timeout: float
) -> list[SpellingSuggestion]:
    """Ask *model* for name corrections across the whole *transcript*, filtered to ones that can apply.

    Unlike Manual Review's glossary suggestions this does not fail open: an LLM failure raises, so
    it is reported rather than silently letting Isolate New Speakers read uncorrected names.
    """
    forms = allowed_name_forms(players)
    if not forms:
        return []
    response_model = _constrained_response_model(forms)
    raw = await call_llm_with_prompt(
        PromptName.SUGGEST_NAME_CORRECTIONS,
        SuggestNameCorrectionsPromptData(transcript=render_transcript(transcript), players=players, allowed_forms=forms),
        model,
        response_model=response_model,
        timeout=timeout,
        # Without strict mode OpenAI treats the schema as a hint and the `to_text` enum is not enforced.
        strict_schema=True,
    )
    proposals = response_model.model_validate_json(raw).suggestions
    suggestions, dropped = filter_name_suggestions(proposals, transcript, forms)
    with widelog.wide_event(op="filter_name_corrections", proposed=len(proposals), kept=len(suggestions), dropped=dict(dropped)):
        pass
    return suggestions


def save_corrected(session_folder: Path, corrections: Sequence[Correction], *, saved_is_current: bool) -> tuple[bool, int]:
    """Apply *corrections* to the cleaned transcript and write the name-corrected transcript (see `save_corrected_transcript`)."""
    return save_corrected_transcript(
        load_source(session_folder), output_path(session_folder), corrections, whole_words=True, saved_is_current=saved_is_current
    )
