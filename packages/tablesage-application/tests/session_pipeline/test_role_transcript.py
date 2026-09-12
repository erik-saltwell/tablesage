from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from tablesage_application.session_pipeline.role_transcript import RoleTranscript, RoleTranscriptUtterance
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _word(text: str, speaker: str, start: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=start + 1, speaker=speaker)


def test_from_transcript_keeps_only_index_speaker_and_preferred_text(tmp_path: Path) -> None:
    source = Transcript.from_words([_word("hello", "Wizard", 0), _word("world", "Rogue", 1)])
    source.utterances[0].punctuated_text = "Hello!"

    compact = RoleTranscript.from_transcript(source)
    path = tmp_path / "role_transcript.json"
    compact.save(path)

    assert RoleTranscript.load(path) == compact
    assert compact.model_dump() == {
        "utterances": [
            {"index": 0, "speaker": "Wizard", "text": "Hello!"},
            {"index": 1, "speaker": "Rogue", "text": "world"},
        ]
    }


def test_from_transcript_falls_back_when_punctuated_text_is_blank() -> None:
    source = Transcript.from_words([_word("hello", "Wizard", 0)])
    source.utterances[0].punctuated_text = "   "

    assert RoleTranscript.from_transcript(source).utterances[0].text == "hello"


@pytest.mark.parametrize("indices", [[1], [0, 2], [0, 0]])
def test_role_transcript_rejects_non_contiguous_indices(indices: list[int]) -> None:
    with pytest.raises(ValidationError, match="zero-based and contiguous"):
        RoleTranscript(utterances=[RoleTranscriptUtterance(index=index, speaker="Wizard", text="Hello") for index in indices])


def test_role_transcript_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RoleTranscriptUtterance.model_validate({"index": 0, "speaker": "Wizard", "text": "Hello", "start": 0.0})
