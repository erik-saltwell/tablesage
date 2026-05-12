from __future__ import annotations

from pydantic import BaseModel

from .._utils import NonEmptyTuple
from .transcribed_utterance import TranscribedUtterance


class Transcript(BaseModel):
    utterances: NonEmptyTuple[TranscribedUtterance]
