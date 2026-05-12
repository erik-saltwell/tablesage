from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, PositiveInt, model_validator

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


class AudioCleaningSettings(BaseModel, frozen=True):
    raw_audio_file: Path = Path("original.m4a")
    cleaned_audio_file: Path = Path("cleaned.wav")
    normalize_volume: bool = False

    @model_validator(mode="after")
    def files_must_differ(self) -> AudioCleaningSettings:
        if self.raw_audio_file == self.cleaned_audio_file:
            msg = "raw_audio_file and cleaned_audio_file must not be the same path"
            raise ValueError(msg)
        return self


class TranscriptionAndDiarizationSettings(BaseModel, frozen=True):
    input_audio_file: Path = Path("cleaned.wav")
    timeout: PositiveInt = 7200
    language_code: ScribeLanguageCode = "eng"
    tag_audio_events: bool = False
    model_id: ScribeModelId = "scribe_v2"


class AppSettings(BaseModel, frozen=True):
    audio_cleaning: AudioCleaningSettings = Field(default_factory=AudioCleaningSettings)
    transcription_and_diarization: TranscriptionAndDiarizationSettings = Field(default_factory=TranscriptionAndDiarizationSettings)
