from __future__ import annotations

from pydantic import BaseModel


class Ledger(BaseModel, frozen=True):
    name: str
