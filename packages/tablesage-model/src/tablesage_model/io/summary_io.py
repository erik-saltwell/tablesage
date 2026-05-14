from __future__ import annotations

from pathlib import Path

from .. import _paths
from ..model.artifacts import Summary


def _summary_file(campaign_slug: str, session_slug: str) -> Path:
    return _paths.session_dir(campaign_slug, session_slug) / _paths.KnownFiles.SUMMARY


def load_summary(campaign_slug: str, session_slug: str) -> Summary:
    file_path: Path = _summary_file(campaign_slug, session_slug)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if not file_path.is_file():
        raise IsADirectoryError(file_path)
    return Summary(markdown=file_path.read_text(encoding="utf-8"))


def save_summary(campaign_slug: str, session_slug: str, summary: Summary) -> None:
    file_path: Path = _summary_file(campaign_slug, session_slug)
    _paths.ensure_dir(file_path.parent)
    if file_path.is_dir():
        raise IsADirectoryError(file_path)
    file_path.write_text(summary.markdown, encoding="utf-8")
