from __future__ import annotations

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr
from .voice_sample import VoiceSample

type PlayerSlug = str


class Player(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr
    voice_samples: tuple[VoiceSample, ...]
    centroid: tuple[float, ...]  # dimension matches VoiceSample.embedding; no length enforcement by design
