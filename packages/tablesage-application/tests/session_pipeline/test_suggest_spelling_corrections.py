from __future__ import annotations

import pytest
from tablesage_application.session_pipeline import suggest_spelling_corrections as suggest_module
from tablesage_application.session_pipeline.suggest_spelling_corrections import (
    SpellingSuggestionProposal,
    SpellingSuggestionsResponse,
    SuggestSpellingCorrectionsPromptData,
    filter_and_dedupe_suggestions,
    suggest_spelling_corrections,
)
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _transcript(*texts: str) -> Transcript:
    """One utterance per supplied text, each on its own speaker so utterances don't merge."""
    utterances = []
    for index, text in enumerate(texts):
        words = [_word(word, f"speaker_{index}", position, position + 1) for position, word in enumerate(text.split())]
        utterances.append(Transcript.from_words(words).utterances[0].model_copy(update={"punctuated_text": text}))
    return Transcript(utterances=utterances)


@pytest.mark.anyio
async def test_calls_llm_once_with_whole_transcript(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript("We reached Zarathiss lonely tower", "Then Alicia said hello")
    captured: dict[str, object] = {}

    async def _capturing_call_llm_with_prompt(
        prompt: object, template_data: SuggestSpellingCorrectionsPromptData, model: str, **kwargs: object
    ) -> str:
        captured["template_data"] = template_data
        captured["model"] = model
        return SpellingSuggestionsResponse(suggestions=[]).model_dump_json()

    monkeypatch.setattr(suggest_module, "call_llm_with_prompt", _capturing_call_llm_with_prompt)

    result = await suggest_spelling_corrections(transcript, ["Zarathis"], ["Alice"], "anthropic/claude-sonnet-4-5")

    assert result == []
    template_data = captured["template_data"]
    assert isinstance(template_data, SuggestSpellingCorrectionsPromptData)
    assert "Zarathiss lonely tower" in template_data.transcript
    assert "Alicia said hello" in template_data.transcript
    assert template_data.glossary == ["Zarathis"]
    assert template_data.attendees == ["Alice"]
    assert captured["model"] == "anthropic/claude-sonnet-4-5"


@pytest.mark.anyio
async def test_returns_raw_proposals_unfiltered(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript("We reached Zarathiss lonely tower")

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return SpellingSuggestionsResponse(
            suggestions=[SpellingSuggestionProposal(from_text="Zarathiss", to_text="Zarathis")]
        ).model_dump_json()

    monkeypatch.setattr(suggest_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await suggest_spelling_corrections(transcript, ["Zarathis"], [], "anthropic/claude-sonnet-4-5")

    assert result == [SpellingSuggestionProposal(from_text="Zarathiss", to_text="Zarathis")]


def test_filter_drops_suggestions_not_found_verbatim() -> None:
    transcript = _transcript("We reached Zarathiss lonely tower")
    proposals = [SpellingSuggestionProposal(from_text="Nonexistent Phrase", to_text="Whatever")]

    assert filter_and_dedupe_suggestions(proposals, transcript) == []


def test_filter_drops_no_op_suggestions() -> None:
    transcript = _transcript("We reached Zarathis lonely tower")
    proposals = [SpellingSuggestionProposal(from_text="Zarathis", to_text="zarathis")]

    assert filter_and_dedupe_suggestions(proposals, transcript) == []


def test_filter_keeps_first_of_duplicate_from_text() -> None:
    transcript = _transcript("We reached Zarathiss lonely tower")
    proposals = [
        SpellingSuggestionProposal(from_text="Zarathiss", to_text="Zarathis"),
        SpellingSuggestionProposal(from_text="Zarathiss", to_text="Zarathas"),
    ]

    result = filter_and_dedupe_suggestions(proposals, transcript)

    assert len(result) == 1
    assert result[0].to_text == "Zarathis"


def test_filter_attaches_case_insensitive_occurrence_count() -> None:
    transcript = _transcript("Zarathiss said hello", "We saw zarathiss again", "Unrelated line")
    proposals = [SpellingSuggestionProposal(from_text="Zarathiss", to_text="Zarathis")]

    result = filter_and_dedupe_suggestions(proposals, transcript)

    assert len(result) == 1
    suggestion = result[0]
    assert suggestion.from_text == "Zarathiss"
    assert suggestion.to_text == "Zarathis"
    assert suggestion.case_sensitive is False
    assert suggestion.occurrence_count == 2
