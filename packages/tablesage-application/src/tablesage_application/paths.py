from __future__ import annotations

from pathlib import Path

# Fixed filenames within a session folder -- the filesystem is the only
# source of truth for artifact existence, there is no `session_artifact`
# table. See `.documentation/import_player_from_filesystem.md`'s sibling doc,
# `.documentation/session_detail_screen.md`.
INPUT_AUDIO_FILENAME = "input_audio.wav"
PROCESSED_SESSION_FILENAME = "processed_session.json"
SESSION_SUMMARY_FILENAME = "summary.md"

AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".m4a", ".flac", ".ogg"})

VOICE_CLIP_GLOB = "*.wav"


def campaigns_root(cwd: Path) -> Path:
    return cwd / ".tablesage" / "campaigns"


def players_root(cwd: Path) -> Path:
    return cwd / ".tablesage" / "players"


def campaign_folder(cwd: Path, campaign_name: str) -> Path:
    return campaigns_root(cwd) / campaign_name


def player_folder(cwd: Path, player_name: str) -> Path:
    return players_root(cwd) / player_name


def session_folder(cwd: Path, campaign_name: str, sequence_number: int) -> Path:
    return campaign_folder(cwd, campaign_name) / f"{sequence_number:03d}"
