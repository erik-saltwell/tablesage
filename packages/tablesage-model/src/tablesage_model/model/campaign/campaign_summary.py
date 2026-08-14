from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr
from .campaign import CampaignState


# CampaignSummary is a computed read-model — it is assembled at read time from a
# campaign's data and is never persisted. It denormalizes the facts the campaign list
# needs to show each campaign at a glance, so the UI doesn't have to open a campaign to
# describe it. A campaign with no sessions yet has None first/last dates and a 0 count.
class CampaignSummary(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr
    state: CampaignState = CampaignState.Active
    description: str = ""
    default_gm: str = ""
    system: str = ""
    first_session_date: date | None = None
    last_session_date: date | None = None
    session_count: int = 0
    player_count: int = 0
