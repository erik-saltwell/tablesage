from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from pydantic import BaseModel, Field

from ..._utils import StrippedNonBlankStr
from ..cast import PlayerSlug, Role


class Session(BaseModel, frozen=True):
    session_date: date
    name: StrippedNonBlankStr
    slug: StrippedNonBlankStr
    attendees: Mapping[PlayerSlug, tuple[Role, ...]] = Field(
        description="Map of player slugs (ids) to the roles they played in this session."
    )
