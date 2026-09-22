from __future__ import annotations

import uuid
from pathlib import Path

from sqlmodel import Session

from ..entities.sessions import list_attendance
from ..paths import ArtifactName
from .artifacts import session_artifacts


def can_process_session(session: Session, session_id: uuid.UUID, session_folder: Path) -> tuple[bool, str | None]:
    """One shared precondition check, usable both for `P`'s enabled/disabled UI state and as a guard inside `process_session` itself."""
    if not session_artifacts(session_folder)[ArtifactName.INPUT_AUDIO]:
        return False, "Import input audio first."

    attendees = list_attendance(session, session_id)
    if len(attendees) < 2:
        return False, "At least 2 attendees are required."

    return True, None


def can_generate_summary(session_folder: Path, previous_session_folder: Path | None = None) -> tuple[bool, str | None]:
    existing = session_artifacts(session_folder)
    if not existing[ArtifactName.LEDGER]:
        return False, "Generate the Ledger first."
    if not existing[ArtifactName.PLAYER_INTRODUCTIONS]:
        return False, "Generate Player Introductions first."
    if previous_session_folder is not None and not session_artifacts(previous_session_folder)[ArtifactName.RECAP_SUMMARY]:
        return False, "Generate the previous Session's Recap Summary first."
    return True, None


def can_clean_session(session_folder: Path) -> tuple[bool, str | None]:
    if not any(session_artifacts(session_folder).values()):
        return False, "No artifacts to delete."
    return True, None
