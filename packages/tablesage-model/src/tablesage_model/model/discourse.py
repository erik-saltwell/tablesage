from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, NonNegativeFloat

from .. import _paths
from .._utils import NonEmptyTuple, StrippedNonBlankStr
from ..protocols import UnassignedSpeaker


class Word(BaseModel, frozen=True):
    text: StrippedNonBlankStr
    start: NonNegativeFloat
    end: NonNegativeFloat
    speaker: StrippedNonBlankStr


class Utterance(BaseModel, frozen=True):
    text: StrippedNonBlankStr
    speaker: StrippedNonBlankStr
    words: NonEmptyTuple[Word]
    embedding: tuple[float, ...] = Field(default_factory=lambda: ())
    similarity_margin: float = 0.0

    @property
    def start(self) -> float:
        return min(word.start for word in self.words)

    @property
    def end(self) -> float:
        return max(word.end for word in self.words)

    @property
    def has_embeddings(self) -> bool:
        return len(self.embedding) > 0

    @property
    def is_unassigned(self) -> bool:
        return self.speaker == UnassignedSpeaker

    def unassign_speaker(self) -> Utterance:
        return self.model_copy(update={"speaker": UnassignedSpeaker})

    def embed(self, embedding: tuple[float, ...]) -> Utterance:
        return self.model_copy(update={"embedding": embedding})

    @staticmethod
    def build_text_from_words(words: Iterable[Word]) -> str:
        return " ".join(word.text for word in words)

    @classmethod
    def from_words(cls, words: Iterable[Word]) -> Utterance:
        new_words: tuple[Word, ...] = tuple(sorted(words, key=lambda word: word.start))

        if len(new_words) == 0:
            msg = "Cannot create TranscribedUtterance with zero words"
            raise ValueError(msg)
        speaker: str = new_words[0].speaker
        if any(word.speaker != speaker for word in new_words):
            msg = "Cannot create TranscribedUtterance from utterance with multiple speakers"
            raise ValueError(msg)
        text: str = cls.build_text_from_words(new_words)
        return cls(text=text, speaker=speaker, words=new_words)


class Discourse(BaseModel, frozen=True):
    utterances: NonEmptyTuple[Utterance]

    @classmethod
    def load(cls, path: str | Path) -> Self:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, path: str | Path) -> None:
        path = Path(path)
        _paths.ensure_dir(path.parent)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
