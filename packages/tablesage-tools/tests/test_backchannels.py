from __future__ import annotations

from tablesage_tools.backchannels import find_backchannel_candidates
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def test_finds_wordlist_match_within_max_words() -> None:
    transcript = Transcript.from_words(
        [
            _word("So", "speaker_0", 0.0, 0.3),
            _word("what", "speaker_0", 0.3, 0.6),
            _word("do", "speaker_0", 0.6, 0.9),
            _word("we", "speaker_0", 0.9, 1.2),
            _word("do", "speaker_0", 1.2, 1.5),
            _word("Yeah", "speaker_1", 1.5, 1.8),
        ]
    )

    assert find_backchannel_candidates(transcript, max_words=3) == [1]


def test_excludes_utterance_over_max_words_even_if_wordlist_prefix_matches() -> None:
    transcript = Transcript.from_words(
        [
            _word("Right", "speaker_0", 0.0, 0.3),
            _word("so", "speaker_0", 0.3, 0.6),
            _word("about", "speaker_0", 0.6, 0.9),
            _word("the", "speaker_0", 0.9, 1.2),
            _word("budget", "speaker_0", 1.2, 1.5),
        ]
    )

    assert find_backchannel_candidates(transcript, max_words=3) == []


def test_excludes_short_utterance_not_in_wordlist() -> None:
    transcript = Transcript.from_words(
        [
            _word("Fireball", "speaker_0", 0.0, 0.5),
        ]
    )

    assert find_backchannel_candidates(transcript, max_words=3) == []


def test_matches_are_normalized_against_punctuated_text() -> None:
    transcript = Transcript.from_words(
        [
            _word("mhm", "speaker_0", 0.0, 0.5),
        ]
    )
    punctuated = transcript.utterances[0].model_copy(update={"punctuated_text": "Mhm."})
    transcript = Transcript(utterances=[punctuated])

    assert find_backchannel_candidates(transcript, max_words=3) == [0]


def test_matches_multi_word_wordlist_entries() -> None:
    transcript = Transcript.from_words(
        [
            _word("Got", "speaker_0", 0.0, 0.3),
            _word("it", "speaker_0", 0.3, 0.6),
        ]
    )

    assert find_backchannel_candidates(transcript, max_words=3) == [0]
