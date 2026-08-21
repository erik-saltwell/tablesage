from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..paths import AUDIO_EXTENSIONS, INPUT_AUDIO_FILENAME, PROCESSED_SESSION_FILENAME, SESSION_SUMMARY_FILENAME


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
