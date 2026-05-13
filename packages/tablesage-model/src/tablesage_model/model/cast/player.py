from __future__ import annotations

from pydantic import BaseModel

from ... import _paths
from .voice_sample import VoiceSample


class Player(BaseModel, frozen=True):
    name: str
    voice_samples: tuple[VoiceSample]
    centroid: list[float]

    @property
    def slug(self) -> str:
        return _paths.slugify(self.name)
