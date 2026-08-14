from __future__ import annotations

from typing import Protocol


class ModelStore:
    pass


class ModelStoreHost(Protocol):
    @property
    def store(self) -> ModelStore: ...
