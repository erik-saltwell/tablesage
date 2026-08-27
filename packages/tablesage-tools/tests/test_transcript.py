from __future__ import annotations

from pathlib import Path

from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def test_utterance_adjusted_defaults_to_false() -> None:
    transcript = Transcript.from_words([_word("hi", "speaker_0", 0.0, 0.5)])

    assert transcript.utterances[0].adjusted is False


def test_utterance_adjusted_survives_a_save_load_round_trip(tmp_path: Path) -> None:
    transcript = Transcript.from_words([_word("hi", "speaker_0", 0.0, 0.5)])
    corrected = transcript.model_copy(deep=True)
    corrected.utterances[0] = corrected.utterances[0].model_copy(update={"speaker": "Alice", "adjusted": True})

    path = tmp_path / "transcript.json"
    corrected.save(path)
    loaded = Transcript.load(path)

    assert loaded.utterances[0].speaker == "Alice"
    assert loaded.utterances[0].adjusted is True
