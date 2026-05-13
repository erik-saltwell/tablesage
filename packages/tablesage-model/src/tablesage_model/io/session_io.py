from __future__ import annotations

from pathlib import Path

from .. import _paths
from ..model.campaign import Session
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
