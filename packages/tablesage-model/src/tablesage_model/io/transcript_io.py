from __future__ import annotations

from pathlib import Path

from .. import _paths
from ..model.transcription import Discourse


def _transcript_file(campaign_slug: str, session_slug: str) -> Path:
    return _paths.session_dir(campaign_slug, session_slug) / _paths.KnownFiles.TRANSCRIPT


def _render_discourse(discourse: Discourse) -> str:
    blocks = [f"**{u.speaker}**: {u.text}" for u in discourse.utterances]
    return "\n\n".join(blocks) + "\n"


def save_transcript(campaign_slug: str, session_slug: str, discourse: Discourse) -> None:
    file_path = _transcript_file(campaign_slug, session_slug)
    _paths.ensure_dir(file_path.parent)
    file_path.write_text(_render_discourse(discourse), encoding="utf-8")
