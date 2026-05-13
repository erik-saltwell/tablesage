from __future__ import annotations

from pydantic import BaseModel

from ... import _paths
from ..cast import Player, Role


class Campaign(BaseModel):
    name: str
    default_gm: str
    players: dict[Player, list[Role]]

    @property
    def slug(self) -> str:
        return _paths.slugify(self.name)
