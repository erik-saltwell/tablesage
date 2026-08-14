from __future__ import annotations

from pathlib import Path

from .. import _paths
from ..model.campaign import SessionSet
from .yaml_io import load_model_from_yaml, save_model_to_yaml


def load_session_set(campaign_slug: str) -> SessionSet:
    file_path: Path = _paths.session_set_file(campaign_slug)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if not file_path.is_file():
        raise IsADirectoryError(file_path)
    return load_model_from_yaml(file_path, SessionSet)


def save_session_set(campaign_slug: str, session_set: SessionSet) -> None:
    file_path: Path = _paths.session_set_file(campaign_slug)
    if file_path.is_dir():
        raise IsADirectoryError(file_path)
    save_model_to_yaml(file_path, session_set)
