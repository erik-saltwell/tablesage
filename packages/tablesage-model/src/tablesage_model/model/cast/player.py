from __future__ import annotations

from pydantic import BaseModel

from .voice_sample import VoiceSample


class Player(BaseModel, frozen=True):
    name: str
    voice_samples: tuple[VoiceSample]
    centroid: list[float]
