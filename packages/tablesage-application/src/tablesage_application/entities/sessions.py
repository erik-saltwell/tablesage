from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from tablesage_model.model import GAME_MASTER_ROLE, CampaignPlayer, Player, SessionAttendance, SessionAttendanceRole
from tablesage_model.model import Session as GameSession

from .._fs import cleanup_orphan_dirs


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
