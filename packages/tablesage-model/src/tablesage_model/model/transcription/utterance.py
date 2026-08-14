from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, Field

from ..._utils import NonEmptyTuple, StrippedNonBlankStr
from ...protocols import UnassignedSpeaker
from ..cast import Embedding
from .word import Word


class Utterance(BaseModel, frozen=True):
    text: StrippedNonBlankStr
    speaker: StrippedNonBlankStr
    words: NonEmptyTuple[Word]
    embedding: Embedding = Field(default_factory=lambda: Embedding(root=()))
    similarity_margin: float = 0.0

    @property
    def start(self) -> float:
        return min(word.start for word in self.words)

    @property
    def end(self) -> float:
        return max(word.end for word in self.words)

    @property
    def has_embeddings(self) -> bool:
        return len(self.embedding.root) > 0

    @property
    def is_unassigned(self) -> bool:
        return self.speaker == UnassignedSpeaker

    def unassign_speaker(self) -> Utterance:
        return self.model_copy(update={"speaker": UnassignedSpeaker})

    def embed(self, embedding: Embedding) -> Utterance:
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
