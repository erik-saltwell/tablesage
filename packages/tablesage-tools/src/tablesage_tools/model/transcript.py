from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

from pydantic import BaseModel, computed_field

from .speech_type import SpeechType


class TranscriptionWord(BaseModel):
    """This is a simple return type that looks similar to the model's TranscribedWord.
    It is used because TranscriptionWord can have non-text speech types while TranscribedWord cannot."""

    text: str
    type: SpeechType
    start: float
    end: float
    speaker: str


class Utterance(BaseModel):
    speaker: str
    start: float
    end: float
    words: list[TranscriptionWord]
    punctuated_text: str | None = None
    # The margin (best-match similarity minus runner-up) from `identify_speakers`'s
    # comparison against attendee centroids -- set for every utterance (assigned or
    # UNASSIGNED_SPEAKER), None only for a transcript produced before this field existed.
    similarity_margin: float | None = None
    # True once a human has changed this utterance's `speaker` via the Speaker Review
    # screen (see `.documentation/speaker_review_screen.md`). Narrower than "reviewed" --
    # confirming an already-correct label, or auto-playing past it untouched, never sets
    # this. Drives the "discard N hand-corrected labels" guard before a re-transcribe.
    adjusted: bool = False

    @computed_field
    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words)

    @classmethod
    def from_words(cls, words: Iterable[TranscriptionWord] | Iterator[TranscriptionWord]) -> Utterance:
        """Build an Utterance from a contiguous run of words, all spoken by the same speaker.

        Raises ValueError if the words don't all share a speaker, or if there are no words.
        """
        word_list = list(words)
        if not word_list:
            raise ValueError("Cannot create an Utterance from an empty sequence of words")

        speaker = word_list[0].speaker
        if any(word.speaker != speaker for word in word_list):
            raise ValueError(f"All words must share a speaker to form an Utterance, got speakers: {[word.speaker for word in word_list]}")

        return cls(
            speaker=speaker,
            start=word_list[0].start,
            end=word_list[-1].end,
            words=word_list,
        )


class Transcript(BaseModel):
    utterances: list[Utterance]

    @classmethod
    def from_words(cls, words: Iterable[TranscriptionWord] | Iterator[TranscriptionWord]) -> Transcript:
        """Build a Transcript by grouping contiguous same-speaker word-type tokens into utterances.

        Spacing and audio-event tokens are dropped entirely (not just ignored for grouping).
        Raises ValueError if this produces no utterances (e.g. silent/no-speech audio).
        """
        groups: list[list[TranscriptionWord]] = []
        for word in words:
            if word.type != SpeechType.WORD:
                continue
            if groups and groups[-1][-1].speaker == word.speaker:
                groups[-1].append(word)
            else:
                groups.append([word])

        if not groups:
            raise ValueError("Cannot create a Transcript with no utterances")

        return cls(utterances=[Utterance.from_words(group) for group in groups])

    def save(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Transcript:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))
