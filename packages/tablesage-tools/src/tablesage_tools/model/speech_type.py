from __future__ import annotations

from enum import StrEnum


class SpeechType(StrEnum):
    WORD = "word"
    SPACING = "spacing"
    AUDIO_EVENT = "audio_event"

    @classmethod
    def _missing_(cls, value: object) -> SpeechType:
        return cls.AUDIO_EVENT
