from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class RegisteredSpeaker(BaseModel, frozen=True):
    name: str
    embedding: list[float]
    included_voice_clips: list[Path]
