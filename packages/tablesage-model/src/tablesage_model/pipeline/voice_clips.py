from __future__ import annotations

from pathlib import Path


def create_voiceprint_dir(voiceprint_slug: str, voiceprint_dir: Path) -> None:
    pass


def delete_voiceprint_dir(voiceprint_slug: str, voiceprint_dir: Path) -> None:
    pass


def add_voiceclips_from_dir(import_dir: Path, voiceprint_slug: str, voiceprint_dir: Path) -> None:
    pass


def add_voiceclips_from_session(session_slug: str, session_dir: Path, voiceprint_slug: str, voiceprint_dir: Path) -> None:
    pass


def compute_voiceprint(voiceprint_slug: str, voiceprint_dir: Path) -> None:
    pass
