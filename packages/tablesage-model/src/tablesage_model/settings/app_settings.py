from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, PositiveInt

type ScribeModelId = Literal["scribe_v1", "scribe_v2"]

type ScribeLanguageCode = Literal[
    "afr",
    "amh",
    "ara",
    "hye",
    "asm",
    "ast",
    "aze",
    "bel",
    "ben",
    "bos",
    "bul",
    "mya",
    "yue",
    "cat",
    "ceb",
    "nya",
    "hrv",
    "ces",
    "dan",
    "nld",
    "eng",
    "est",
    "fil",
    "fin",
    "fra",
    "ful",
    "glg",
    "lug",
    "kat",
    "deu",
    "ell",
    "guj",
    "hau",
    "heb",
    "hin",
    "hun",
    "isl",
    "ibo",
    "ind",
    "gle",
    "ita",
    "jpn",
    "jav",
    "kea",
    "kan",
    "kaz",
    "khm",
    "kor",
    "kur",
    "kir",
    "lao",
    "lav",
    "lin",
    "lit",
    "luo",
    "ltz",
    "mkd",
    "msa",
    "mal",
    "mlt",
    "zho",
    "mri",
    "mar",
    "mon",
    "nep",
    "nso",
    "nor",
    "oci",
    "ori",
    "pus",
    "fas",
    "pol",
    "por",
    "pan",
    "ron",
    "rus",
    "srp",
    "sna",
    "snd",
    "slk",
    "slv",
    "som",
    "spa",
    "swa",
    "swe",
    "tam",
    "tgk",
    "tel",
    "tha",
    "tur",
    "ukr",
    "umb",
    "urd",
    "uzb",
    "vie",
    "cym",
    "wol",
    "xho",
    "zul",
]


class SpeakerIdentificationSettings(BaseModel, frozen=True):
    input_audio_file: Path = Path("cleaned.wav")
    similarity_residual_threshold: float = 0.2


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
