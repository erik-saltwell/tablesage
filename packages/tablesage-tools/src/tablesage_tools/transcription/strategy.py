from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..model import Transcript


class TranscriptionStrategy(Protocol):
    """A speech-to-text provider that transcribes and diarizes one audio file.

    Provider-specific options (model, language, timeouts) belong to the implementation's
    constructor, so callers depend only on the audio and the expected speaker count.
    """

    async def transcribe_and_diarize(self, input_file: Path, speaker_count: int | None) -> Transcript:
        """Transcribe `input_file` into anonymously diarized utterances; `speaker_count` is a hint when given."""
        ...
