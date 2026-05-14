from __future__ import annotations

from pydantic import RootModel


class Embedding(RootModel[tuple[float, ...]], frozen=True):
    """A speaker-embedding vector (typically 192-d, L2-normalized)."""

    def __len__(self) -> int:
        return len(self.root)
