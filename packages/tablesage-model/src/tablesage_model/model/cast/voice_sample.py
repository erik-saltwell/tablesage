from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .embedding import Embedding
from .provenance import ProvenanceType


class VoiceSample(BaseModel, frozen=True):
    filepath: Path
    embedding: Embedding
    provenance_type: ProvenanceType
    source: str
    index: int
