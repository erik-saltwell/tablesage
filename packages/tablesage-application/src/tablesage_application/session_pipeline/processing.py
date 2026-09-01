from __future__ import annotations

import uuid
from pathlib import Path

from sqlmodel import Session
from tablesage_model.model import Player

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

    missing = [attendee.player_name for attendee in attendees if not _player_has_centroid(session, attendee.player_id)]
    if missing:
        return False, f"Missing voice profile for: {', '.join(missing)}."

    return True, None


def _player_has_centroid(session: Session, player_id: uuid.UUID) -> bool:
    player = session.get(Player, player_id)
    return player is not None and player.centroid_embedding is not None


def can_generate_summary(session_folder: Path) -> tuple[bool, str | None]:
    if not session_artifacts(session_folder)[ArtifactName.ROLE_TRANSCRIPT]:
        return False, "Clean the transcript first."
    return True, None
