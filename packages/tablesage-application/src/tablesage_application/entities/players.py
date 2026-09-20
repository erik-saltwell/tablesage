from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from tablesage_model.model import Player, SessionAttendance
from tablesage_model.player_names import validate_player_name

from .._fs import cleanup_orphan_dirs, create_named_entity_folder, rename_named_entity


def create_player(session: Session, player: Player, players_root: Path) -> Player:
    validate_player_name(player.name)
    session.add(player)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(f"A player named '{player.name}' already exists.") from exc

    try:
        create_named_entity_folder(players_root, player.name, kind="player")
    except ValueError:
        session.rollback()
        raise

    return player


def list_players(session: Session) -> list[Player]:
    return list(session.exec(select(Player)).all())


def get_player(session: Session, player_id: uuid.UUID) -> Player:
    player = session.get(Player, player_id)
    if player is None:
        raise ValueError("Player not found.")
    return player


def rename_player(session: Session, player_id: uuid.UUID, new_name: str, players_root: Path) -> Player:
    player = get_player(session, player_id)
    rename_named_entity(session, player, new_name, players_root, kind="player")
    player.updated_at = datetime.now(UTC)
    return player


def can_delete_player(session: Session, player_id: uuid.UUID) -> tuple[bool, str | None]:
    """Whether ``player_id`` can be deleted -- false once they have attended any session.

    Checked up front so the UI can explain the block before asking for
    confirmation, rather than only discovering it via `delete_player`'s
    `IntegrityError` fallback after the user has already confirmed.
    """
    has_attended = session.exec(select(SessionAttendance.id).where(SessionAttendance.player_id == player_id).limit(1)).first() is not None
    if has_attended:
        return False, "This player has attended one or more sessions and cannot be deleted. Remove their attendance first."
    return True, None


def delete_player(session: Session, player_id: uuid.UUID) -> None:
    player = get_player(session, player_id)
    session.delete(player)
    try:
        session.flush()
    except IntegrityError as exc:
        # Defense in depth: `can_delete_player` is the UI's up-front check, but attendance
        # could change between that check and this call (e.g. a concurrent session), so the
        # constraint here remains the actual guarantee.
        session.rollback()
        raise ValueError("This player has attended sessions and cannot be deleted.") from exc


def cleanup_orphan_player_dirs(session: Session, players_root: Path) -> list[str]:
    known_names = {player.name for player in list_players(session)}
    return cleanup_orphan_dirs(players_root, known_names)
