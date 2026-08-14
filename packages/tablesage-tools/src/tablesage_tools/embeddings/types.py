from __future__ import annotations

from pydantic import RootModel


class Embedding(RootModel[tuple[float, ...]], frozen=True):
    """A speaker-embedding vector (typically 192-d, L2-normalized).

    This is tools' own generic embedding type, structurally identical to but
    independent of any domain model's Embedding type. Callers convert at the
    application boundary.
    """

    def __len__(self) -> int:
        return len(self.root)
