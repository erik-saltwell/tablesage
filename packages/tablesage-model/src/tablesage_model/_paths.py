from __future__ import annotations

import os
import re
import uuid
from enum import StrEnum
from pathlib import Path

from platformdirs import user_data_dir


class KnownFiles(StrEnum):
    SETTINGS = "settings.yaml"
    CAMPAIGN = "campaign_data.yaml"
    PLAYER = "player.yaml"
    SESSION = "session.yaml"
    TRANSCRIPT = "transcript.md"
    DISCOURSE = "discourse.json"
    SUMMARY = "summary.md"
    TRACE = "trace.json"
    LOGFILE = "tablesage.log"
    SESSION_SET = "sessions.yaml"
    CAMPAIGN_SET = "campaigns.yaml"
    PLAYER_SET = "players.yaml"


class KnownDirectories(StrEnum):
    CAMPAIGNS = "campaigns"
    SESSIONS = "sessions"
    PLAYERS = "players"
    VOICE_CLIPS = "voice_clips"
    CANDIDATE_CLIPS = "candidates"
    LOGS = "logs"


def data_root() -> Path:
    override = os.environ.get("TABLESAGE_DATA_DIR")
    if override:
        return Path(override).expanduser()
    return Path(user_data_dir("tablesage", "tablesage"))


def slugify(name: str) -> str:
    """Convert a display name to a filesystem-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_settings_path() -> Path:
    return data_root() / KnownFiles.SETTINGS


def campaign_set_file() -> Path:
    return data_root() / KnownFiles.CAMPAIGN_SET


def campaigns_dir() -> Path:
    return data_root() / KnownDirectories.CAMPAIGNS


def campaign_dir(campaign_slug: str) -> Path:
    return campaigns_dir() / campaign_slug


def campaign_file(campaign_slug: str) -> Path:
    return campaign_dir(campaign_slug) / KnownFiles.CAMPAIGN


def sessions_dir(campaign_slug: str) -> Path:
    return campaign_dir(campaign_slug=campaign_slug) / KnownDirectories.SESSIONS


def session_dir(campaign_slug: str, session_slug: str) -> Path:
    return sessions_dir(campaign_slug=campaign_slug) / session_slug


def session_file(campaign_slug: str, session_slug: str) -> Path:
    return session_dir(campaign_slug, session_slug) / KnownFiles.SESSION


def trace_path() -> Path:
    return data_root() / KnownDirectories.LOGS / KnownFiles.TRACE


def logfile_path() -> Path:
    return data_root() / KnownDirectories.LOGS / KnownFiles.LOGFILE


def session_set_file(campaign_slug: str) -> Path:
    return campaign_dir(campaign_slug) / KnownFiles.SESSION_SET


def players_dir(campaign_slug: str) -> Path:
    return campaign_dir(campaign_slug) / KnownDirectories.PLAYERS


def player_set_file(campaign_slug: str) -> Path:
    return players_dir(campaign_slug) / KnownFiles.PLAYER_SET


def player_dir(campaign_slug: str, player_slug: str) -> Path:
    return players_dir(campaign_slug) / player_slug


def player_file(campaign_slug: str, player_slug: str) -> Path:
    return player_dir(campaign_slug, player_slug) / KnownFiles.PLAYER


def voice_clips_dir(campaign_slug: str, player_slug: str) -> Path:
    return player_dir(campaign_slug, player_slug) / KnownDirectories.VOICE_CLIPS


def generate_voice_sample_filename() -> str:
    return f"{uuid.uuid4().hex}.wav"


def to_absolute(base_path: Path, final_path: Path) -> Path:
    if final_path.is_absolute():
        return final_path
    return base_path / final_path
