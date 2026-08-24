from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ArtifactName(Enum):
    """Every artifact a session folder can hold. Adding a new one means adding an entry to `ARTIFACTS` below --
    that's what makes it show up in `session_artifacts()` and in `invalidate_downstream()`."""

    INPUT_AUDIO = "input_audio"
    PROCESSED_SESSION = "processed_session"
    SUMMARY = "summary"
    TRANSCRIPT = "transcript"
    TRANSCRIPT_TEXT = "transcript_text"
    TRANSCRIPT_ROLES_TEXT = "transcript_roles_text"


class ArtifactCategory(Enum):
    """How an artifact is produced, for `invalidate_downstream()` to decide what a change makes stale.

    IMPORTED artifacts are never invalidated -- they're the source, not a derivative. FROM_AUDIO
    artifacts are derived (directly or transitively) from the input audio. FROM_LOG artifacts are
    derived from the canonical session log (not yet built -- see `.documentation` when it exists).
    """

    IMPORTED = "imported"
    FROM_AUDIO = "from_audio"
    FROM_LOG = "from_log"


@dataclass(frozen=True)
class ArtifactSpec:
    filename: str
    category: ArtifactCategory
    should_show_in_ui: bool
    display_name: str


# Fixed filenames within a session folder -- the filesystem is the only
# source of truth for artifact existence, there is no `session_artifact`
# table. See `.documentation/import_player_from_filesystem.md`'s sibling doc,
# `.documentation/session_detail_screen.md`.
#
# Order here is pipeline order, and drives both the indicator panel's layout
# and `should_show_in_ui`'s filtering -- entries stay in this order whether
# or not they're shown.
ARTIFACTS: dict[ArtifactName, ArtifactSpec] = {
    ArtifactName.INPUT_AUDIO: ArtifactSpec(
        "input_audio.wav", ArtifactCategory.IMPORTED, should_show_in_ui=True, display_name="Input Audio"
    ),
    ArtifactName.TRANSCRIPT: ArtifactSpec(
        "transcript.json", ArtifactCategory.FROM_AUDIO, should_show_in_ui=False, display_name="Transcript (JSON)"
    ),
    ArtifactName.TRANSCRIPT_TEXT: ArtifactSpec(
        "transcript.md", ArtifactCategory.FROM_AUDIO, should_show_in_ui=True, display_name="Transcript"
    ),
    ArtifactName.TRANSCRIPT_ROLES_TEXT: ArtifactSpec(
        "transcript_roles.md", ArtifactCategory.FROM_AUDIO, should_show_in_ui=False, display_name="Transcript (Roles)"
    ),
    ArtifactName.PROCESSED_SESSION: ArtifactSpec(
        "processed_session.json", ArtifactCategory.FROM_AUDIO, should_show_in_ui=False, display_name="Processed Session"
    ),
    # Today's `can_generate_summary` gate reads `has_processed_session`, so this is FROM_AUDIO --
    # it'll move to FROM_LOG once `generate_summary` is rewired to read the canonical log instead.
    ArtifactName.SUMMARY: ArtifactSpec("summary.md", ArtifactCategory.FROM_AUDIO, should_show_in_ui=True, display_name="Summary"),
}

AUDIO_EXTENSIONS = frozenset({".wav", ".mp3", ".m4a", ".flac", ".ogg"})

VOICE_CLIP_GLOB = "*.wav"


def campaigns_root(cwd: Path) -> Path:
    return cwd / ".tablesage" / "campaigns"


def players_root(cwd: Path) -> Path:
    return cwd / ".tablesage" / "players"


def logs_root(cwd: Path) -> Path:
    return cwd / ".tablesage" / "logs"


def campaign_folder(cwd: Path, campaign_name: str) -> Path:
    return campaigns_root(cwd) / campaign_name


def player_folder(cwd: Path, player_name: str) -> Path:
    return players_root(cwd) / player_name


def session_folder(cwd: Path, campaign_name: str, sequence_number: int) -> Path:
    return campaign_folder(cwd, campaign_name) / f"{sequence_number:03d}"
