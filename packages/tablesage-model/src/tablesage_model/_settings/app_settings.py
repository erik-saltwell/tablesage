from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, PositiveInt

from .type_aliases import ScribeLanguageCode, ScribeModelId


class SpeakerIdentificationSettings(BaseModel, frozen=True):
    input_audio_file: Path = Path("cleaned.wav")
    similarity_margin_threshold: float = 0.1


class AudioCleaningSettings(BaseModel, frozen=True):
    raw_audio_file: Path = Path("original.m4a")
    normalize_volume: bool = False


class TranscriptionAndDiarizationSettings(BaseModel, frozen=True):
    timeout: PositiveInt = 7200
    language_code: ScribeLanguageCode = "eng"
    tag_audio_events: bool = False
    model_id: ScribeModelId = "scribe_v2"


class AppSettings(BaseModel, frozen=True):
    audio_cleaning: AudioCleaningSettings = Field(default_factory=AudioCleaningSettings)
    transcription_and_diarization: TranscriptionAndDiarizationSettings = Field(default_factory=TranscriptionAndDiarizationSettings)
    speaker_identification: SpeakerIdentificationSettings = Field(default_factory=SpeakerIdentificationSettings)
    cleaned_audio_file: Path = Path("cleaned.wav")
