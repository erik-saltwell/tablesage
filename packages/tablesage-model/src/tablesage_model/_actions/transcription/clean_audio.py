from __future__ import annotations

from pathlib import Path

from ..._tools.ffmpeg import clean_clip
from ...protocols import PhasedProgressEvent, PhasedProgressSink
from ...settings import AppSettings


async def _progress(sink: PhasedProgressSink, phase: str) -> None:
    event: PhasedProgressEvent = PhasedProgressEvent(source="audio_cleaner", phase=phase)
    await sink.publish(event)


async def clean_audio(campaign_slug: str, session_slug: str, app_settings: AppSettings, sink: PhasedProgressSink) -> None:
    await clean_audio_raw(
        input_audio_file=app_settings.input_audio_file,
        cleaned_audio_file=app_settings.audio_cleaning.cleaned_audio_file,
        normalize_volume=app_settings.audio_cleaning.normalize_volume,
        sink=sink,
    )


async def clean_audio_raw(
    input_audio_file: Path,
    cleaned_audio_file: Path,
    normalize_volume: bool,
    sink: PhasedProgressSink,
) -> None:

    if not input_audio_file.exists():
        raise FileNotFoundError(input_audio_file)

    await _progress(sink, "cleaning audio")
    await clean_clip(input_audio_file, cleaned_audio_file, normalize=normalize_volume)
