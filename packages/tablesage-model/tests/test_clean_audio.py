from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from tablesage_model import _paths
from tablesage_model._actions.transcription.clean_audio import clean_audio
from tablesage_model._settings import AppSettings
from tablesage_model._tools import ffmpeg
from tablesage_model.io import save_session
from tablesage_model.model.campaign import Session
from tablesage_model.protocols import NullPhasedProgressSink


@pytest.mark.anyio
async def test_clean_audio_reads_source_path_from_session_audio_filename(monkeypatch: pytest.MonkeyPatch) -> None:
    campaign_slug = "sable-crown"
    session_slug = "session-one"
    audio_filename = "session-one-raw.m4a"

    session = Session(
        session_date=date(2026, 5, 13),
        name="Session One",
        slug=session_slug,
        audio_filename=audio_filename,
        attendees={"ada": ("Game Master",)},
    )
    save_session(campaign_slug, session)

    session_dir = _paths.session_dir(campaign_slug, session_slug)
    expected_source = session_dir / audio_filename
    expected_source.write_bytes(b"fake-audio")

    captured: dict[str, Path] = {}

    async def fake_convert_to_48k_wav(source: Path, target: Path) -> None:
        captured["source"] = source
        target.write_bytes(b"wav")

    async def fake_enhance(source: Path, target: Path) -> None:
        target.write_bytes(b"enhanced")

    async def fake_convert_to_16k(source: Path, target: Path) -> None:
        target.write_bytes(b"16k")

    monkeypatch.setattr(ffmpeg, "convert_to_48k_wav", fake_convert_to_48k_wav)
    monkeypatch.setattr(ffmpeg, "enhance_with_mossformer2", fake_enhance)
    monkeypatch.setattr(ffmpeg, "convert_to_16k_mono", fake_convert_to_16k)

    await clean_audio(campaign_slug, session_slug, AppSettings(), NullPhasedProgressSink())

    assert captured["source"] == expected_source
