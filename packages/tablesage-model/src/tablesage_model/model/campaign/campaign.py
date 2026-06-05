from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr
from .glossary_entry import GlossaryEntry


class CampaignState(StrEnum):
    Active = ("active",)
    Archived = "archived"


class Campaign(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr
    description: str = ""
    default_gm: str = ""
    system: str = ""
    state: CampaignState = CampaignState.Active
    glossary: tuple[GlossaryEntry, ...] = ()
