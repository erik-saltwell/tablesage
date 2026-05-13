from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class VoiceSample(BaseModel, frozen=True):
    filename: Path
    embedding: tuple[float, ...]  # dimension matches Player.centroid; no length enforcement by design
