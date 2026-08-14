from __future__ import annotations

from pydantic import BaseModel


class Summary(BaseModel, frozen=True):
    markdown: str
