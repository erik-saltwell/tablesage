from __future__ import annotations

from typing import Protocol

UnassignedSpeaker: str = "Unidentified Speaker"


class SpeechRun(Protocol):
    @property
    def start(self) -> float: ...

    @property
    def end(self) -> float: ...

    @property
    def speaker(self) -> str: ...

    @property
    def text(self) -> str: ...
