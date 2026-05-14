from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from .embedding import Embedding


class VoiceSample(BaseModel, frozen=True):
    filepath: Path
    embedding: Embedding
