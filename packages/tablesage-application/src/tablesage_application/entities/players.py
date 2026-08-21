from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from tablesage_model.model import Player

from .._fs import cleanup_orphan_dirs, create_named_entity_folder, rename_named_entity


def create_player(session: Session, player: Player, players_root: Path) -> Player:
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
    return player


def delete_player(session: Session, player_id: uuid.UUID) -> None:
    player = get_player(session, player_id)
    session.delete(player)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError("This player has attended sessions and cannot be deleted.") from exc


def cleanup_orphan_player_dirs(session: Session, players_root: Path) -> list[str]:
    known_names = {player.name for player in list_players(session)}
    return cleanup_orphan_dirs(players_root, known_names)
