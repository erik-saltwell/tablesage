from __future__ import annotations

from pydantic import BaseModel


class Transcript(BaseModel, frozen=True):
    name: str
