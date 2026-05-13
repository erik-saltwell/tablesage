from __future__ import annotations

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr


# PlayerName is an intentional lightweight index entry — it intentionally omits the
# full Player fields so the display name can be updated independently of player data.
class PlayerName(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr


class PlayerSet(BaseModel, frozen=True):
    players: tuple[PlayerName, ...]
