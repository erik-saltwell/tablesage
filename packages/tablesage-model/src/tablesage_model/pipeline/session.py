from __future__ import annotations

import asyncio
import shutil
from enum import StrEnum
from pathlib import Path

import yaml

from tablesage_model.model import Player

from .. import _paths
from .._actions.transcription.clean_audio import clean_audio
from .._actions.transcription.identify_speakers import identify_speakers as _identify_speakers
from .._actions.transcription.transcribe_and_diarize import transcribe_and_diarize as _transcribe_and_diarize
from .._utils import run_command
from ..model.discourse import Discourse
from ..protocols import IncrementalProgressSink, PhasedProgressEvent, PhasedProgressSink
from ..settings import AppSettings


class OrphanAttendeeError(Exception):
    def __init__(self, missing_slugs: tuple[str, ...]) -> None:
        self.missing_slugs = missing_slugs
        super().__init__(f"Session attendees reference player slugs not in PlayerSet: {', '.join(missing_slugs)}")


class SessionState(StrEnum):
    new = "new"
    audio_imported = "audio imported"
    partially_processed = "partially processed"
    fully_processed = "fully processed"
    transcribed_and_diarized = "transcribed and diarized"
    speakers_identified = "speakers identified"


async def _ensure_dir(path: Path) -> Path:
    await asyncio.to_thread(path.mkdir, parents=True, exist_ok=True)
    return path


async def _to_absolute(base_path: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return base_path / path


async def _save_session_state(sessions_dir: Path, state: SessionState) -> None:
    await asyncio.to_thread((sessions_dir / _KnownSessionFiles.state_file).write_text, f"{state.value}\n", encoding="utf-8")


async def _check_state(allowed_states: list[SessionState], session_slug: str, sessions_dir: Path) -> None:
    state: SessionState = await get_session_state(session_slug=session_slug, sessions_dir=sessions_dir)
    if state in allowed_states:
        msg: str = f"Current state {state} cannot be one of ({', '.join(allowed_states)})."
        raise RuntimeError(msg)


async def _check_not_state(disallowed_states: list[SessionState], session_slug: str, sessions_dir: Path) -> None:
    state: SessionState = await get_session_state(session_slug=session_slug, sessions_dir=sessions_dir)
    if state not in disallowed_states:
        msg: str = f"Current state {state} must be one of ({', '.join(disallowed_states)})."
        raise RuntimeError(msg)


class _KnownSessionFiles(StrEnum):
    settings_file = "settings.yaml"
    state_file = "state.yaml"


async def _emit(sink: PhasedProgressSink, phase: str) -> None:
    await sink.publish(PhasedProgressEvent(source="process_session", phase=phase))


async def create_session(settings: AppSettings, session_slug: str, sessions_dir: Path) -> None:
    session_dir: Path = sessions_dir / session_slug
    await _ensure_dir(session_dir)
    await _save_session_state(session_dir, SessionState.new)
    await asyncio.to_thread(settings.save, session_dir / _KnownSessionFiles.settings_file)


async def clean_session(settings: AppSettings, campaign_slug: str, session_slug: str, sessions_dir: Path, sink: PhasedProgressSink) -> None:
    await _check_not_state([SessionState.new], session_slug=session_slug, sessions_dir=sessions_dir)
    await clean_audio(campaign_slug, session_slug, settings, sink)
    await _save_session_state(sessions_dir, SessionState.audio_imported)


async def import_audio_file(audio_filepath: Path, session_slug: str, sessions_dir: Path) -> None:
    session_dir = sessions_dir / session_slug
    settings = await asyncio.to_thread(AppSettings.load, session_dir / _KnownSessionFiles.settings_file)
    target_path = await _to_absolute(session_dir, settings.input_audio_file)
    await _ensure_dir(target_path.parent)

    if audio_filepath.suffix.lower() == target_path.suffix.lower():
        if audio_filepath.resolve() != target_path.resolve():
            await asyncio.to_thread(shutil.copy2, audio_filepath, target_path)
    else:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(audio_filepath),
            str(target_path),
        ]
        await asyncio.to_thread(run_command, cmd)

    await _save_session_state(session_dir, SessionState.audio_imported)


async def transcribe_and_diarize(
    settings: AppSettings, player_slugs: list[str], campaign_slug: str, session_slug: str, sessions_dir: Path, sink: PhasedProgressSink
) -> None:
    await _check_state([SessionState.audio_imported], session_slug, sessions_dir)
    speakers: int | None = len(player_slugs) if player_slugs else None
    discourse: Discourse = await _transcribe_and_diarize(
        campaign_slug=campaign_slug, session_slug=session_slug, app_settings=settings, speaker_count=speakers, sink=sink
    )
    discourse.save(sessions_dir / session_slug / _paths.KnownFiles.DISCOURSE)
    await _save_session_state(sessions_dir=sessions_dir, state=SessionState.transcribed_and_diarized)


async def identify_speakers_by_voice(
    settings: AppSettings, attendees: list[Player], campaign_slug: str, session_slug: str, sessions_dir: Path, sink: IncrementalProgressSink
) -> None:
    await _check_state([SessionState.transcribed_and_diarized], session_slug, sessions_dir)
    session: Discourse = Discourse.load(sessions_dir / session_slug / _paths.KnownFiles.DISCOURSE)
    discourse: Discourse = await _identify_speakers(
        campaign_slug=campaign_slug, session_slug=session_slug, app_settings=settings, attendees=attendees, session_set=session, sink=sink
    )
    discourse.save(sessions_dir / session_slug / _paths.KnownFiles.DISCOURSE)
    await _save_session_state(sessions_dir, SessionState.speakers_identified)


async def get_session_state(session_slug: str, sessions_dir: Path) -> SessionState:
    state_file = sessions_dir / session_slug / _KnownSessionFiles.state_file
    state = await asyncio.to_thread(state_file.read_text, encoding="utf-8")
    return SessionState(yaml.safe_load(state))
