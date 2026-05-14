from __future__ import annotations

from pathlib import Path

from .. import _paths
from ..model.transcription import Discourse


def _discourse_file(campaign_slug: str, session_slug: str) -> Path:
    return _paths.session_dir(campaign_slug, session_slug) / _paths.KnownFiles.DISCOURSE


def save_discourse(campaign_slug: str, session_slug: str, discourse: Discourse) -> None:
    file_path = _discourse_file(campaign_slug, session_slug)
    _paths.ensure_dir(file_path.parent)
    file_path.write_text(discourse.model_dump_json(indent=2), encoding="utf-8")


def load_discourse(campaign_slug: str, session_slug: str) -> Discourse:
    file_path = _discourse_file(campaign_slug, session_slug)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    return Discourse.model_validate_json(file_path.read_text(encoding="utf-8"))
