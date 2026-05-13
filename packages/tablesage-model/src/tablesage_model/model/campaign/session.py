from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from ... import _paths
from ..cast import Player, Role


class Session(BaseModel):
    session_date: date
    name: str
    attendees: dict[Player, list[Role]]

    @property
    def slug(self) -> str:
        return _paths.slugify(self.name)
