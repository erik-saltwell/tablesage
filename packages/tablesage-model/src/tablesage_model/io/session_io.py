from __future__ import annotations

import shutil
from pathlib import Path

from .. import _paths
from ..model.campaign import Session, SessionSet
from .session_set_io import load_session_set, save_session_set
from .yaml_io import load_model_from_yaml, save_model_to_yaml


def load_session(campaign_slug: str, session_slug: str) -> Session:
    file_path: Path = _paths.session_file(campaign_slug, session_slug)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if not file_path.is_file():
        raise IsADirectoryError(file_path)
    session = load_model_from_yaml(file_path, Session)
    if session.slug != session_slug:
        raise ValueError(f"Slug mismatch: directory is '{session_slug}', file says '{session.slug}'")
    return session


def save_session(campaign_slug: str, session: Session) -> None:
    file_path: Path = _paths.session_file(campaign_slug, session.slug)
    if file_path.is_dir():
        raise IsADirectoryError(file_path)
    save_model_to_yaml(file_path, session)


def delete_session(campaign_slug: str, session_slug: str) -> None:
    current = load_session_set(campaign_slug)
    remaining = tuple(s for s in current.sessions if s.slug != session_slug)
    save_session_set(campaign_slug, SessionSet(sessions=remaining))


def cleanup_orphan_session_dirs(campaign_slug: str) -> tuple[str, ...]:
    root = _paths.sessions_dir(campaign_slug)
    if not root.exists():
        return ()
    known = {s.slug for s in load_session_set(campaign_slug).sessions}
    deleted: list[str] = []
    for child in sorted(root.iterdir()):
        if child.is_dir() and child.name not in known:
            shutil.rmtree(child)
            deleted.append(child.name)
    return tuple(deleted)
