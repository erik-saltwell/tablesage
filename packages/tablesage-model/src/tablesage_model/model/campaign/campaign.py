from __future__ import annotations

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr
from .glossary_entry import GlossaryEntry


class Campaign(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr
    default_gm: str = ""
    glossary: tuple[GlossaryEntry, ...] = ()
