from __future__ import annotations

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr
from .embedding import Embedding
from .voice_sample import VoiceSample

type PlayerSlug = str


class Player(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr
    voice_samples: tuple[VoiceSample, ...]
    centroid: Embedding
