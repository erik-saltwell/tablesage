from __future__ import annotations

from pathlib import Path

from ... import _paths
from ..._tools.ffmpeg import clean_clip
from ...io import load_session
from ...protocols import PhasedProgressEvent, PhasedProgressSink
from ...settings import AppSettings, AudioCleaningSettings


async def _progress(sink: PhasedProgressSink, phase: str) -> None:
    event: PhasedProgressEvent = PhasedProgressEvent(source="audio_cleaner", phase=phase)
    await sink.publish(event)


async def clean_audio(campaign_slug: str, session_slug: str, app_settings: AppSettings, sink: PhasedProgressSink) -> None:
    settings: AudioCleaningSettings = app_settings.audio_cleaning
    session_dir: Path = _paths.session_dir(campaign_slug, session_slug)
    session = load_session(campaign_slug, session_slug)
    source_path: Path = session_dir / session.audio_filename
    cleaned_output_path: Path = _paths.to_absolute(session_dir, app_settings.cleaned_audio_file)
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    await _progress(sink, "cleaning audio")
    await clean_clip(source_path, cleaned_output_path, normalize=settings.normalize_volume)
