from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel


class ProvenanceType(StrEnum):
    INFERRED = "inferred"
    SESSION_ENHANCEMENT = "session_enhancement"
    IMPORT = "import"


class VoiceSample(BaseModel, frozen=True):
    filepath: Path
    embedding: tuple[float, ...]
    provenance_type: ProvenanceType
    source: str
    index: int
