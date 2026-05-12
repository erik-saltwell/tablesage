from __future__ import annotations

from pathlib import Path

from .._tools import eleven_labs


async def transcribe_and_diarize() -> None:
    await eleven_labs.transcribe_and_diarize(Path(""), "eng", "", 7200, False, None)
