from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from tablesage_model.model import GAME_MASTER_ROLE, CampaignPlayer, Player, SessionAttendance, SessionAttendanceRole
from tablesage_model.model import Session as GameSession

from ._fs import cleanup_orphan_dirs

# Fixed filenames within a session folder -- the filesystem is the only
# source of truth for artifact existence, there is no `session_artifact`
# table. See `.documentation/import_player_from_filesystem.md`'s sibling doc,
# `.documentation/session_detail_screen.md`.
INPUT_AUDIO_FILENAME = "input_audio.wav"
PROCESSED_SESSION_FILENAME = "processed_session.json"
SESSION_SUMMARY_FILENAME = "summary.md"


def create_session(session: Session, campaign_id: uuid.UUID, name: str, session_date: date | None, campaign_folder: Path) -> GameSession:
    max_sequence = session.exec(select(func.max(GameSession.sequence_number)).where(GameSession.campaign_id == campaign_id)).one()
    next_sequence = (max_sequence or 0) + 1

    game_session = GameSession(campaign_id=campaign_id, sequence_number=next_sequence, name=name, session_date=session_date)
    session.add(game_session)
    session.flush()

    folder = campaign_folder / f"{next_sequence:03d}"
    folder.mkdir(parents=True, exist_ok=False)

    return game_session


def list_sessions(session: Session, campaign_id: uuid.UUID) -> list[GameSession]:
    return list(session.exec(select(GameSession).where(GameSession.campaign_id == campaign_id)).all())


def get_session(session: Session, session_id: uuid.UUID) -> GameSession:
    game_session = session.get(GameSession, session_id)
    if game_session is None:
        raise ValueError("Session not found.")
    return game_session


def update_session(session: Session, session_id: uuid.UUID, name: str, session_date: date | None) -> GameSession:
    game_session = get_session(session, session_id)
    game_session.name = name
    game_session.session_date = session_date
    session.flush()
    return game_session


def delete_session(session: Session, session_id: uuid.UUID) -> None:
    """Delete the `Session` row (and its attendance/roles, via FK cascade).

    Matches the soft-delete convention used elsewhere in this app: this is a
    DB-only delete, the on-disk session folder is left in place as an orphan
    -- cleaning it up is `cleanup_orphan_session_dirs`'s job, not this one's.
    """
    game_session = get_session(session, session_id)
    session.delete(game_session)


def cleanup_orphan_session_dirs(session: Session, campaign_id: uuid.UUID, campaign_folder: Path) -> list[str]:
    known_names = {f"{game_session.sequence_number:03d}" for game_session in list_sessions(session, campaign_id)}
    return cleanup_orphan_dirs(campaign_folder, known_names)


# Artifacts / indicators


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


AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".m4a", ".flac", ".ogg"})


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


# Attendance


@dataclass(frozen=True)
class Attendee:
    attendance_id: uuid.UUID
    player_id: uuid.UUID
    player_name: str
    roles: tuple[str, ...]


def _seed_role_name(default_role_name: str) -> str:
    return "Game Master" if default_role_name == GAME_MASTER_ROLE else default_role_name


def list_attendance(session: Session, session_id: uuid.UUID) -> list[Attendee]:
    rows = session.exec(
        select(SessionAttendance, Player).where(SessionAttendance.session_id == session_id).where(SessionAttendance.player_id == Player.id)
    ).all()

    attendees = []
    for attendance, player in rows:
        roles = session.exec(select(SessionAttendanceRole.name).where(SessionAttendanceRole.attendance_id == attendance.id)).all()
        attendees.append(Attendee(attendance_id=attendance.id, player_id=player.id, player_name=player.name, roles=tuple(sorted(roles))))
    return attendees


def add_attendance(session: Session, campaign_id: uuid.UUID, session_id: uuid.UUID, player_id: uuid.UUID) -> Attendee:
    membership = session.exec(
        select(CampaignPlayer).where(CampaignPlayer.campaign_id == campaign_id).where(CampaignPlayer.player_id == player_id)
    ).first()
    if membership is None:
        raise ValueError("This player is not a member of the campaign roster.")

    attendance = SessionAttendance(session_id=session_id, player_id=player_id)
    session.add(attendance)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("This player is already attending the session.") from exc

    seed_role = _seed_role_name(membership.default_role_name)
    session.add(SessionAttendanceRole(attendance_id=attendance.id, name=seed_role))
    session.flush()

    player = session.get(Player, player_id)
    assert player is not None
    return Attendee(attendance_id=attendance.id, player_id=player_id, player_name=player.name, roles=(seed_role,))


def add_attendance_with_roles(
    session: Session, campaign_id: uuid.UUID, session_id: uuid.UUID, player_id: uuid.UUID, roles: list[str]
) -> Attendee:
    """Create a new attendance row for `player_id`, then set its role list to `roles`.

    Combines `add_attendance` (which seeds one default role from the
    campaign membership) with `set_attendance_roles` (which overwrites it) --
    the caller is the attendee dialog, where roles are chosen directly, so
    the end result should be exactly the roles the user picked, not the
    seeded default plus them.
    """
    attendee = add_attendance(session, campaign_id, session_id, player_id)
    return set_attendance_roles(session, attendee.attendance_id, roles)


def set_attendance_player(session: Session, campaign_id: uuid.UUID, attendance_id: uuid.UUID, player_id: uuid.UUID) -> Attendee:
    """Reassign an existing attendance row to a different roster player."""
    attendance = session.get(SessionAttendance, attendance_id)
    if attendance is None:
        raise ValueError("Attendance not found.")

    membership = session.exec(
        select(CampaignPlayer).where(CampaignPlayer.campaign_id == campaign_id).where(CampaignPlayer.player_id == player_id)
    ).first()
    if membership is None:
        raise ValueError("This player is not a member of the campaign roster.")

    attendance.player_id = player_id
    session.add(attendance)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("This player is already attending the session.") from exc

    player = session.get(Player, player_id)
    assert player is not None
    roles = session.exec(select(SessionAttendanceRole.name).where(SessionAttendanceRole.attendance_id == attendance_id)).all()
    return Attendee(attendance_id=attendance_id, player_id=player_id, player_name=player.name, roles=tuple(sorted(roles)))


def remove_attendance(session: Session, attendance_id: uuid.UUID) -> None:
    attendance = session.get(SessionAttendance, attendance_id)
    if attendance is None:
        raise ValueError("Attendance not found.")
    session.delete(attendance)


def set_attendance_roles(session: Session, attendance_id: uuid.UUID, roles: list[str]) -> Attendee:
    attendance = session.get(SessionAttendance, attendance_id)
    if attendance is None:
        raise ValueError("Attendance not found.")

    cleaned = [role.strip() for role in roles if role.strip()]
    if not cleaned:
        raise ValueError("At least one role is required.")

    for existing in session.exec(select(SessionAttendanceRole).where(SessionAttendanceRole.attendance_id == attendance_id)).all():
        session.delete(existing)
    session.flush()

    for name in cleaned:
        session.add(SessionAttendanceRole(attendance_id=attendance_id, name=name))
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("Duplicate role names are not allowed.") from exc

    player = session.get(Player, attendance.player_id)
    assert player is not None
    return Attendee(attendance_id=attendance_id, player_id=attendance.player_id, player_name=player.name, roles=tuple(cleaned))
