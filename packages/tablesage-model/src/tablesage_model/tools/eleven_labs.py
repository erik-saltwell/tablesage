from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from elevenlabs import AsyncElevenLabs, SpeechToTextChunkResponseModel


class WordType(StrEnum):
    WORD = "word"
    SPACING = "spacing"
    AUDIO_EVENT = "audio_event"

    @classmethod
    def _missing_(cls, value: object) -> WordType:
        return cls.AUDIO_EVENT


@dataclass
class TranscriptionWords:
    text: str
    type: WordType
    start: float
    end: float
    speaker_id: str


async def transcribe_and_diarize(
    input_file: Path, language_code: str, model_id: str, request_timeout: int, tag_audio_events: bool, speaker_count: int | None
) -> list[TranscriptionWords]:
    elevenlabs: AsyncElevenLabs = AsyncElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
    )
    transcription: SpeechToTextChunkResponseModel
    with input_file.open("rb") as audio_data:
        if speaker_count:
            transcription = await elevenlabs.speech_to_text.convert(
                file=audio_data,
                model_id=model_id,
                tag_audio_events=tag_audio_events,
                language_code=language_code,
                diarize=True,
                timestamps_granularity="word",
                num_speakers=speaker_count,
                request_options={"timeout_in_seconds": request_timeout},
            )
        else:
            transcription = await elevenlabs.speech_to_text.convert(
                file=audio_data,
                model_id=model_id,
                tag_audio_events=tag_audio_events,
                language_code=language_code,
                diarize=True,
                timestamps_granularity="word",
                request_options={"timeout_in_seconds": request_timeout},
            )
    return [
        TranscriptionWords(text=word.text, type=WordType(word.type), start=word.start, end=word.end, speaker_id=word.speaker_id)
        for word in transcription.words
    ]
