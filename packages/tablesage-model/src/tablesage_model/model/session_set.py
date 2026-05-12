from __future__ import annotations

from pydantic import BaseModel

from .._utils import NonEmptyTuple
from .session_utterance import SessionUtterance


class SessionSet(BaseModel, frozen=True):
    utterances: NonEmptyTuple[SessionUtterance]
