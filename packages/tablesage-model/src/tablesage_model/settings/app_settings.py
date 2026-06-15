from __future__ import annotations

from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel, Field, PositiveInt

from .. import _paths
from .type_aliases import ScribeLanguageCode, ScribeModelId

# class RemoveOutliersSettings(BaseModel, frozen=True):
#     min_sample_similarity: float = Field(default=0.6, gt=0, le=1)
#     min_samples: PositiveInt = 5


class SpeakerIdentificationSettings(BaseModel, frozen=True):
    similarity_margin_threshold: float = 0.1
    identified_discourse_file: Path = Path("identified.json")


class AudioCleaningSettings(BaseModel, frozen=True):
    cleaned_audio_file: Path = Path("cleaned.wav")
    normalize_volume: bool = False


class TranscriptionAndDiarizationSettings(BaseModel, frozen=True):
    timeout: PositiveInt = 7200
    language_code: ScribeLanguageCode = "eng"
    tag_audio_events: bool = False
    model_id: ScribeModelId = "scribe_v2"
    transcribed_discourse_file: Path = Path("transcribed.json")


# class EnhanceVoicesSettings(BaseModel, frozen=True):
#     min_margin_for_voice_sample: float = 0.15
#     min_clip_seconds: float = 1.0
#     max_clip_seconds: float = 8.0


class SummaryGeneratorSettings(BaseModel, frozen=True):
    llm_model: str = "anthropic/claude-sonnet-4-5"
    summary_file: Path = Path("summary.md")


class AppSettings(BaseModel, frozen=True):
    input_audio_file: Path = Path("input.wav")
    audio_cleaning: AudioCleaningSettings = Field(default_factory=AudioCleaningSettings)
    transcription_and_diarization: TranscriptionAndDiarizationSettings = Field(default_factory=TranscriptionAndDiarizationSettings)
    speaker_identification: SpeakerIdentificationSettings = Field(default_factory=SpeakerIdentificationSettings)
    #    remove_outliers: RemoveOutliersSettings = Field(default_factory=RemoveOutliersSettings)
    #    enhance_voices: EnhanceVoicesSettings = Field(default_factory=EnhanceVoicesSettings)
    #    llm_model: str = "anthropic/claude-sonnet-4-5"
    #    clean_clips_on_import: bool = False

    @classmethod
    def load(cls, path: str | Path | None = None) -> Self:
        path = _paths.app_settings_path() if path is None else Path(path)
        if not path.exists():
            return cls()
        with open(path, encoding="utf-8") as f:
            data: Any = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"Empty or blank YAML file: {path}")
        return cls.model_validate(data)

    def save(self, path: str | Path | None = None) -> None:
        path = _paths.app_settings_path() if path is None else Path(path)
        _paths.ensure_dir(path.parent)
        data: dict[str, Any] = self.model_dump(mode="json")

        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
