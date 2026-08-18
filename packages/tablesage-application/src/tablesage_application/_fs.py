from __future__ import annotations

import shutil
from pathlib import Path
from typing import Protocol

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


class _NamedEntity(Protocol):
    name: str


def create_named_entity_folder(root: Path, name: str, *, kind: str) -> None:
    """Create ``root/name``, raising a friendly error if it already exists."""
    root.mkdir(parents=True, exist_ok=True)
    folder = root / name
    try:
        folder.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"A {kind} folder named '{name}' already exists on disk.") from exc


def rename_named_entity(session: Session, entity: _NamedEntity, new_name: str, root: Path, *, kind: str) -> None:
    """Rename ``entity.name`` in the DB and its on-disk folder as one operation.

    Both succeed or neither does: the DB change is flushed (not committed)
    first, then the filesystem rename is attempted; either failure rolls
    back the DB change.
    """
    old_name = entity.name
    if new_name == old_name:
        return

    entity.name = new_name
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ValueError(f"A {kind} named '{new_name}' already exists.") from exc

    old_folder = root / old_name
    new_folder = root / new_name
    try:
        old_folder.rename(new_folder)
    except OSError as exc:
        session.rollback()
        raise ValueError(f"Could not rename {kind} folder: {exc}") from exc


def cleanup_orphan_dirs(root: Path, known_names: set[str]) -> list[str]:
    """Remove folders under ``root`` that aren't in ``known_names``.

    Returns the names of the removed folders.
    """
    if not root.exists():
        return []

    removed: list[str] = []
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and entry.name not in known_names:
            shutil.rmtree(entry)
            removed.append(entry.name)
    return removed
