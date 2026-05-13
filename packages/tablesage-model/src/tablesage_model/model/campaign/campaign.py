from __future__ import annotations

from pydantic import BaseModel

from ..cast import Player, Role


class Campaign(BaseModel):
    name: str
    slug: str
    default_gm: str
    players: dict[Player, list[Role]]
