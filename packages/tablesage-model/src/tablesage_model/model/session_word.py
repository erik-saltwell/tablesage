from __future__ import annotations

from pydantic import BaseModel, NonNegativeFloat

from .._utils import StrippedNonBlankStr


class SessionWord(BaseModel, frozen=True):
    text: StrippedNonBlankStr
    start: NonNegativeFloat
    end: NonNegativeFloat
    speaker: StrippedNonBlankStr
