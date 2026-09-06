from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from tablesage_tools.model import Transcript

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RoleTranscriptUtterance(BaseModel):
    """One compact, addressable utterance in the role-attributed transcript."""

    model_config = ConfigDict(extra="forbid")

    index: int = Field(ge=0)
    speaker: NonEmptyText
    text: NonEmptyText


class RoleTranscript(BaseModel):
    """The compact transcript used by every post-review LLM pass."""

    model_config = ConfigDict(extra="forbid")

    utterances: list[RoleTranscriptUtterance]

    @model_validator(mode="after")
    def _require_contiguous_indices(self) -> Self:
        indices = [utterance.index for utterance in self.utterances]
        expected = list(range(len(self.utterances)))
        if indices != expected:
            raise ValueError(f"Role transcript indices must be zero-based and contiguous; expected {expected}, got {indices}.")
        return self

    @classmethod
    def from_transcript(cls, transcript: Transcript) -> Self:
        utterances = []
        for index, utterance in enumerate(transcript.utterances):
            punctuated_text = utterance.punctuated_text
            text = punctuated_text if punctuated_text is not None and punctuated_text.strip() else utterance.text
            utterances.append(RoleTranscriptUtterance(index=index, speaker=utterance.speaker, text=text))
        return cls(utterances=utterances)

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, path: Path) -> None:
        path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")
