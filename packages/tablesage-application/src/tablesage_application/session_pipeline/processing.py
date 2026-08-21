from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session
from tablesage_model.model import Player

from ..entities.sessions import list_attendance
from ..paths import AUDIO_EXTENSIONS, INPUT_AUDIO_FILENAME, PROCESSED_SESSION_FILENAME, SESSION_SUMMARY_FILENAME


@dataclass(frozen=True)
class SessionArtifacts:
    """What exists on disk for a session -- drives the indicator panel and the P/G gates."""

    has_input_audio: bool
    has_processed_session: bool
    has_summary: bool


def session_artifacts(session_folder: Path) -> SessionArtifacts:
    return SessionArtifacts(
        has_input_audio=(session_folder / INPUT_AUDIO_FILENAME).is_file(),
        has_processed_session=(session_folder / PROCESSED_SESSION_FILENAME).is_file(),
        has_summary=(session_folder / SESSION_SUMMARY_FILENAME).is_file(),
    )


def invalidate_downstream(session_folder: Path) -> None:
    """Delete derived artifacts (processed session, summary) -- never the raw input audio.

    Public (not module-private) because every destructive edit invalidates:
    re-importing audio, adding/removing an attendee, editing roles, and
    (in Phase 11) rerunning Process -- all call this directly.
    """
    (session_folder / PROCESSED_SESSION_FILENAME).unlink(missing_ok=True)
    (session_folder / SESSION_SUMMARY_FILENAME).unlink(missing_ok=True)


def validate_import_source(source_path: Path) -> None:
    """Raise if `source_path` isn't a file with a recognized audio extension.

    A fast-fail UX check only -- the actual cleaning pipeline (ffmpeg) can
    handle far more than this list, but session recordings plausibly arrive
    as any of these common recorder/voice-memo formats, unlike the player
    voice-clip import's `.wav`-only source directories.
    """
    if not source_path.is_file():
        raise ValueError(f"'{source_path}' is not a file.")
    if source_path.suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError(f"'{source_path.name}' isn't a recognized audio file.")


def import_audio(source_path: Path, session_folder: Path, clean: Callable[[Path, Path], None]) -> None:
    """Clean `source_path` into the session folder as the fixed input-audio file.

    `clean(source, target)` is injected so this stays decoupled from the
    concrete (async, ffmpeg/ML-backed) cleaning tool -- see `Application._clean_session_audio`.
    Cleaned into a temp file in the same folder first, so a failed/partial
    clean never corrupts an existing `input_audio.wav`; downstream artifacts
    (processed session, summary) are only invalidated once the clean has
    actually succeeded, so a failure leaves prior processing intact instead
    of destroying it for nothing.
    """
    if not source_path.is_file():
        raise ValueError(f"'{source_path}' is not a file.")
    session_folder.mkdir(parents=True, exist_ok=True)

    temp_target = session_folder / f".{INPUT_AUDIO_FILENAME}.tmp"
    try:
        clean(source_path, temp_target)
    except Exception:
        temp_target.unlink(missing_ok=True)
        raise

    invalidate_downstream(session_folder)
    temp_target.replace(session_folder / INPUT_AUDIO_FILENAME)


# Process/Generate preconditions


def can_process_session(session: Session, session_id: uuid.UUID, session_folder: Path) -> tuple[bool, str | None]:
    """One shared precondition check, usable both for `P`'s enabled/disabled UI state and as a guard inside `process_session` itself."""
    if not session_artifacts(session_folder).has_input_audio:
        return False, "Import input audio first."

    attendees = list_attendance(session, session_id)
    if len(attendees) < 2:
        return False, "At least 2 attendees are required."

    missing = [attendee.player_name for attendee in attendees if not _player_has_centroid(session, attendee.player_id)]
    if missing:
        return False, f"Missing voice profile for: {', '.join(missing)}."

    return True, None


def _player_has_centroid(session: Session, player_id: uuid.UUID) -> bool:
    player = session.get(Player, player_id)
    return player is not None and player.centroid_embedding is not None


def can_generate_summary(session_folder: Path) -> tuple[bool, str | None]:
    if not session_artifacts(session_folder).has_processed_session:
        return False, "Process the session first."
    return True, None
