from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from tablesage_application.player_import_from_audio import ProposeResult, SpeakerCandidate


@dataclass
class SpeakerResolution:
    """Stage 4's working per-speaker resolution -- mutable, held in `PlayerImportRun.resolutions`.

    `player_id is None` means "New Player", named `player_name`.
    """

    player_id: uuid.UUID | None
    player_name: str
    excluded: bool = False


@dataclass
class PlayerImportRun:
    """The "import players from audio" flow's shared, mutable state.

    Owned by the flow itself (not any one `Screen`) -- see the design doc's "Run context"
    concept. Threaded by reference into each stage screen's constructor so popping a screen
    to go back never loses what the user already entered.
    """

    source_audio_path: Path
    clip_dir: Path | None = None
    candidates: list[SpeakerCandidate] = field(default_factory=list)
    speaker_count: int | None = None
    propose_result: ProposeResult | None = None
    resolutions: dict[str, SpeakerResolution] = field(default_factory=dict)
