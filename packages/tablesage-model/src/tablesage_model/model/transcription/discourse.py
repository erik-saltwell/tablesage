from __future__ import annotations

from pydantic import BaseModel

from ..._utils import NonEmptyTuple
from .utterance import Utterance


class Discourse(BaseModel, frozen=True):
    utterances: NonEmptyTuple[Utterance]
