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

from .._fs import cleanup_orphan_dirs, create_named_entity_folder


def next_sequence_number(session: Session, campaign_id: uuid.UUID) -> int:
    """The sequence number the next session created for `campaign_id` would be assigned.

    Shared by `create_session` and the folder-collision preflight check
    (`Application.session_folder_would_collide`) so both agree on which
    on-disk slot ("NNN") is about to be used.
    """
    max_sequence = session.exec(select(func.max(GameSession.sequence_number)).where(GameSession.campaign_id == campaign_id)).one()
    return (max_sequence or 0) + 1


def create_session(session: Session, campaign_id: uuid.UUID, name: str, session_date: date | None, campaign_folder: Path) -> GameSession:
    next_sequence = next_sequence_number(session, campaign_id)

    game_session = GameSession(campaign_id=campaign_id, sequence_number=next_sequence, name=name, session_date=session_date)
    session.add(game_session)
    session.flush()

    try:
        create_named_entity_folder(campaign_folder, f"{next_sequence:03d}", kind="session")
    except ValueError:
        session.rollback()
        raise

    return game_session


def list_sessions(session: Session, campaign_id: uuid.UUID) -> list[GameSession]:
    return list(session.exec(select(GameSession).where(GameSession.campaign_id == campaign_id)).all())


def get_session(session: Session, session_id: uuid.UUID) -> GameSession:
    game_session = session.get(GameSession, session_id)
    if game_session is None:
        raise ValueError("Session not found.")
    return game_session


def get_previous_session(session: Session, game_session: GameSession) -> GameSession | None:
    """Return the preceding Session in campaign-local chronological order.

    Dated Sessions sort first by date and then by sequence number. Undated Sessions sort after
    dated Sessions and use sequence number among themselves, giving the ordering a deterministic
    fallback when dates are unavailable.
    """
    campaign_sessions = list_sessions(session, game_session.campaign_id)
    ordered = sorted(
        campaign_sessions,
        key=lambda candidate: (
            candidate.session_date is None,
            candidate.session_date or date.max,
            candidate.sequence_number,
        ),
    )
    position = next(index for index, candidate in enumerate(ordered) if candidate.id == game_session.id)
    return ordered[position - 1] if position else None


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


def seed_attendance_from_previous_session_or_roster(session: Session, campaign_id: uuid.UUID, new_session_id: uuid.UUID) -> list[Attendee]:
    """Populate a newly-created session's attendance from the campaign's most recent prior session.

    Falls back to seeding one attendee per campaign roster member (each getting
    their `CampaignPlayer.default_role_name`, via `add_attendance`) when there is
    no prior session -- i.e. this is the campaign's first. When a prior session
    exists, each of its attendees' full role list is carried over verbatim
    instead, since that's a strictly richer source than the roster's one
    default role per player. A player who was removed from the roster since the
    prior session is silently skipped rather than failing the whole import --
    `add_attendance` enforces roster membership, and a stale carry-over
    shouldn't block creating the new session.
    """
    other_sessions = session.exec(
        select(GameSession).where(GameSession.campaign_id == campaign_id).where(GameSession.id != new_session_id)
    ).all()
    previous_session = max(other_sessions, key=lambda s: s.sequence_number, default=None)

    if previous_session is None:
        memberships = session.exec(select(CampaignPlayer).where(CampaignPlayer.campaign_id == campaign_id)).all()
        return [add_attendance(session, campaign_id, new_session_id, membership.player_id) for membership in memberships]

    seeded: list[Attendee] = []
    for attendee in list_attendance(session, previous_session.id):
        try:
            seeded.append(add_attendance_with_roles(session, campaign_id, new_session_id, attendee.player_id, list(attendee.roles)))
        except ValueError:
            continue
    return seeded


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
