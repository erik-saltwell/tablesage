from __future__ import annotations

from pathlib import Path

# The artifact and processing-stage registries live in their own modules; they are re-exported here
# because `paths` is the long-standing import point for them.
from .artifact_registry import (
    ARTIFACTS,
    LEDGER_PAIR_MARKER,
    SUMMARY_INPUTS_FILENAME,
    ArtifactCategory,
    ArtifactName,
    ArtifactSpec,
    artifacts_for_stage,
)
from .processing_stages import (
    NEW_PLAYER_STAGES,
    ProcessingBlocker,
    SessionProcessingStage,
    SessionProcessingStageID,
    get_processing_stages,
)

__all__ = [
    "ARTIFACTS",
    "AUDIO_EXTENSIONS",
    "LEDGER_PAIR_MARKER",
    "NEW_PLAYER_STAGES",
    "SUMMARY_INPUTS_FILENAME",
    "VOICE_CLIP_GLOB",
    "ArtifactCategory",
    "ArtifactName",
    "ArtifactSpec",
    "ProcessingBlocker",
    "SessionProcessingStage",
    "SessionProcessingStageID",
    "artifacts_for_stage",
    "campaign_folder",
    "campaigns_root",
    "get_processing_stages",
    "logs_root",
    "player_folder",
    "players_root",
    "session_folder",
]


AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".m4a", ".flac", ".ogg"})

VOICE_CLIP_GLOB = "*.wav"


def campaigns_root(cwd: Path) -> Path:
    return cwd / "campaigns"


def players_root(cwd: Path) -> Path:
    return cwd / "players"


def logs_root(cwd: Path) -> Path:
    return cwd / ".tablesage" / "logs"


def campaign_folder(cwd: Path, campaign_name: str) -> Path:
    return campaigns_root(cwd) / campaign_name


def player_folder(cwd: Path, player_name: str) -> Path:
    return players_root(cwd) / player_name


def session_folder(cwd: Path, campaign_name: str, sequence_number: int) -> Path:
    return campaign_folder(cwd, campaign_name) / f"{sequence_number:03d}"
