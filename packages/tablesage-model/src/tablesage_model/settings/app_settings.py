from __future__ import annotations

from pydantic import BaseModel, Field, PositiveInt

from .type_aliases import ScribeLanguageCode, ScribeModelId


class RemoveOutliersSettings(BaseModel, frozen=True):
    min_sample_similarity: float = Field(default=0.6, gt=0, le=1)
    min_samples: PositiveInt = 5


class SpeakerIdentificationSettings(BaseModel, frozen=True):
    similarity_margin_threshold: float = 0.1
    log_diagnostics: bool = False
    # When False, an utterance is never left UNASSIGNED_SPEAKER just because its best-vs-runner-up
    # similarity margin fell below similarity_margin_threshold -- the best match is taken
    # regardless of confidence. Utterances too short to embed at all are unaffected: they're
    # still assigned UNASSIGNED_SPEAKER either way, since there's no embedding-based judgment to
    # skip there in the first place.
    allow_unassigned: bool = True


class AudioCleaningSettings(BaseModel, frozen=True):
    normalize_volume: bool = False


class SessionAudioImportSettings(BaseModel, frozen=True):
    normalize_volume: bool = False


class TranscriptionAndDiarizationSettings(BaseModel, frozen=True):
    timeout: PositiveInt = 7200
    language_code: ScribeLanguageCode = "eng"
    tag_audio_events: bool = False
    model_id: ScribeModelId = "scribe_v2"


class EnhanceVoicesSettings(BaseModel, frozen=True):
    min_margin_for_voice_sample: float = 0.15
    min_clip_seconds: float = 1.0
    max_clip_seconds: float = 8.0


class RemoveBackchannelsSettings(BaseModel, frozen=True):
    enabled: bool = False
    max_words: PositiveInt = 3


class AppSettings(BaseModel, frozen=True):
    audio_cleaning: AudioCleaningSettings = Field(default_factory=AudioCleaningSettings)
    transcription_and_diarization: TranscriptionAndDiarizationSettings = Field(default_factory=TranscriptionAndDiarizationSettings)
    speaker_identification: SpeakerIdentificationSettings = Field(default_factory=SpeakerIdentificationSettings)
    remove_outliers: RemoveOutliersSettings = Field(default_factory=RemoveOutliersSettings)
    enhance_voices: EnhanceVoicesSettings = Field(default_factory=EnhanceVoicesSettings)
    remove_backchannels: RemoveBackchannelsSettings = Field(default_factory=RemoveBackchannelsSettings)
    llm_model: str = "anthropic/claude-sonnet-4-5"
    llm_model_lite: str = "anthropic/claude-haiku-4-5"
    clean_clips_on_import: bool = False
    session_audio_import: SessionAudioImportSettings = Field(default_factory=SessionAudioImportSettings)
