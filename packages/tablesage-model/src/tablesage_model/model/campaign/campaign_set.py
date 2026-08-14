from __future__ import annotations

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr


# CampaignName is an intentional lightweight index entry — it intentionally omits the
# full Campaign fields so the display name can be updated independently of campaign data.
class CampaignName(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr


class CampaignSet(BaseModel, frozen=True):
    campaigns: tuple[CampaignName, ...]
