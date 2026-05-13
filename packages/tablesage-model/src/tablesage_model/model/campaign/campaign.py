from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, Field

from ..._utils import StrippedNonBlankStr
from ..cast import PlayerSlug, Role


class Campaign(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr
    default_gm: StrippedNonBlankStr
    players: Mapping[PlayerSlug, tuple[Role, ...]] = Field(
        description="Map of player slugs (ids) to the roles they have played in the campaign"
    )
