from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path

from platformdirs import user_data_dir


class KnownFiles(StrEnum):
    SETTINGS = "settings.yaml"
    CAMPAIGN = "campaign_data.yaml"
    PLAYER_SETTINGS = "player.yaml"
    CENTROID = "centroid.npy"
    SESSION = "session.yaml"
    TRANSCRIPT = "transcript.md"
    SUMMARY = "summary.md"
    TRACE = "trace.json"
    LOGFILE = "tablesage.log"


class KnownDirectories(StrEnum):
    CAMPAIGNS = "campaigns"
    SESSIONS = "sessions"
    TRASH = ".trash"
    PLAYERS = "players"
    VOICE_CLIPS = "voice_clips"
    CANDIDATE_CLIPS = "candidates"
    LOGS = "logs"


def data_root() -> Path:
    override = os.environ.get("TABLESAGE_DATA_DIR")
    if override:
        return Path(override)
    return Path(user_data_dir("tablesage", "tablesage"))


def slugify(name: str) -> str:
    """Convert a display name to a filesystem-safe slug."""
    import re

    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def app_settings_path() -> Path:
    return data_root() / KnownFiles.SETTINGS


def campaigns_dir() -> Path:
    return data_root() / KnownDirectories.CAMPAIGNS


def campaign_dir(campaign_slug: str) -> Path:
    return campaigns_dir() / campaign_slug


def sessions_dir(campaign_slug: str) -> Path:
    return campaign_dir(campaign_slug=campaign_slug) / KnownDirectories.SESSIONS


def session_dir(campaign_slug: str, session_slug: str) -> Path:
    return sessions_dir(campaign_slug=campaign_slug) / session_slug


def trace_path() -> Path:
    return data_root() / KnownDirectories.LOGS / KnownFiles.TRACE


def logfile_path() -> Path:
    return data_root() / KnownDirectories.LOGS / KnownFiles.LOGFILE
