from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr


class KnownRoles(StrEnum):
    GM = "Game Master"


class Role(BaseModel, frozen=True):
    name: StrippedNonBlankStr
