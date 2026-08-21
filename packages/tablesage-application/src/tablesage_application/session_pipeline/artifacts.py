from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..paths import INPUT_AUDIO_FILENAME, PROCESSED_SESSION_FILENAME, SESSION_SUMMARY_FILENAME


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
