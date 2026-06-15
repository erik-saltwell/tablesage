from __future__ import annotations

from pydantic import BaseModel

from .._utils import StrippedNonBlankStr
from .embedding import Embedding

type PlayerSlug = str


class Player(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr
    centroid: Embedding
