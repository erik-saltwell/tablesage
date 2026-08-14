from __future__ import annotations

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr


class GlossaryEntry(BaseModel, frozen=True):
    term: StrippedNonBlankStr
    description: str
