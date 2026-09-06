from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ArtifactName(Enum):
    """Every artifact a session folder can hold. Adding a new one means adding an entry to `ARTIFACTS` below --
    that's what makes it show up in `session_artifacts()` and in `invalidate_downstream()`."""

    INPUT_AUDIO = "input_audio"
    LEDGER = "ledger"
    SUMMARY = "summary"
    TRANSCRIPT = "transcript"
    TRANSCRIPT_TEXT = "transcript_text"
    TRANSCRIPT_ROLES_TEXT = "transcript_roles_text"
    TRANSCRIPT_BENCHMARK = "transcript_benchmark"
    REVIEWED_TRANSCRIPT = "reviewed_transcript"
    ROLE_TRANSCRIPT = "role_transcript"
    TRANSCRIPT_SECTIONS = "transcript_sections"
    PLAYER_INTRODUCTIONS = "player_introductions"
    RECAP_SUMMARY = "recap_summary"


class ArtifactCategory(Enum):
    """How an artifact is produced, for `invalidate_downstream()` to decide what a change makes stale.

    IMPORTED artifacts are never invalidated -- they're the source, not a derivative. FROM_AUDIO
    artifacts are derived (directly or transitively) from the input audio. FROM_TRANSCRIPT
    artifacts are derived from the current transcript. FROM_LOG artifacts are derived from the
    Ledger.
    """

    IMPORTED = "imported"
    FROM_AUDIO = "from_audio"
    FROM_TRANSCRIPT = "from_transcript"
    FROM_LOG = "from_log"


@dataclass(frozen=True)
class ArtifactSpec:
    filename: str
    category: ArtifactCategory
    should_show_in_ui: bool
    display_name: str
    companion_filenames: tuple[str, ...] = ()


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
        # Legacy Summary-generation input. Transcription no longer creates this artifact;
        # a transcript rebuild still invalidates any older copy. Ledger generation renders
        # the preferred transcript to role-attributed Markdown in memory instead.
        "transcript_roles.md",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Transcript (Roles)",
    ),
    # A benchmark-only derivative of TRANSCRIPT with too-short-to-identify utterances stripped
    # (see `session_pipeline.transcript_review.generate_benchmark_transcript`) -- generated on
    # demand, never hand-edited, never read back by any other pipeline step. It is invalidated
    # alongside the reviewed transcript whenever the source transcript is rebuilt.
    ArtifactName.TRANSCRIPT_BENCHMARK: ArtifactSpec(
        "transcript_benchmark.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Transcript (Benchmark)",
    ),
    # A completed Manual Review. It is deliberately separate from the machine-produced
    # transcript and is invalidated whenever that source transcript is rebuilt or the audio
    # (or attendance that influences speaker identification) changes.
    ArtifactName.REVIEWED_TRANSCRIPT: ArtifactSpec(
        "transcript_reviewed.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Reviewed Transcript",
    ),
    # Backchannel-cleaned, role-attributed transcript written by the Clean Transcript step (see
    # `session_pipeline.clean_transcript`). Ledger generation reads this directly instead of
    # rendering its own role-attributed text.
    ArtifactName.ROLE_TRANSCRIPT: ArtifactSpec(
        "role_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Role Transcript",
    ),
    ArtifactName.TRANSCRIPT_SECTIONS: ArtifactSpec(
        "transcript_sections.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Transcript Sections",
    ),
    ArtifactName.LEDGER: ArtifactSpec(
        "ledger.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Ledger",
        companion_filenames=("ledger.md",),
    ),
    ArtifactName.PLAYER_INTRODUCTIONS: ArtifactSpec(
        "player_introductions.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Player Introductions",
    ),
    ArtifactName.RECAP_SUMMARY: ArtifactSpec(
        "recap_summary.md",
        ArtifactCategory.FROM_LOG,
        should_show_in_ui=True,
        display_name="Recap Summary",
    ),
    ArtifactName.SUMMARY: ArtifactSpec("summary.md", ArtifactCategory.FROM_LOG, should_show_in_ui=True, display_name="Summary"),
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
