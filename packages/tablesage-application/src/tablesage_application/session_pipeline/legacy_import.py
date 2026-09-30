"""One-time import of a Session processed before `processing_state.json` existed.

The retired modification-time graph decides which artifacts were current (see `Application._import_legacy_sessions`).
This module turns the rest of the old folder into sections:

- The four old receipt and decision files become the sections they now are.
- Steps that did not exist then (suggestions and decisions split out of the review steps, the import request, the
  voice-print offer) get placeholder sections marked `"legacy": true`, wherever the work they now precede was
  current. That keeps completed work complete. A placeholder's suggestions are empty, so a step reopened on an
  imported Session re-runs its suggestion step first (see the TUI's processing steps).
- A completed transcript review becomes its edit list, so reopening it shows the review as it was left.

The old files move to the Session's `legacy/` folder rather than being deleted.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from tablesage_tools.model import Transcript

from ..paths import ARTIFACTS, ArtifactName
from . import transcript_edits
from .session_processing import REVIEW_DRAFT_FILENAME

LEGACY_DIRNAME = "legacy"

# Old files that are now sections, folded in as they are.
_FOLDED: tuple[ArtifactName, ...] = (
    ArtifactName.NEW_SPEAKER_ASSIGNMENTS,
    ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS,
    ArtifactName.SEEDED_VOICE_SAMPLES,
    ArtifactName.EXTRACTED_GLOSSARY_TERMS,
)


def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _file(folder: Path, name: ArtifactName) -> Path:
    return folder / ARTIFACTS[name].filename


def build_sections(folder: Path, current: set[ArtifactName]) -> tuple[dict[str, Any], set[ArtifactName]]:
    """The sections for an imported folder, and which of them stand for current work (so their steps are recorded
    complete). `current` is what the retired graph found current."""
    sections: dict[str, Any] = {}
    carried: set[ArtifactName] = set()

    def placeholder(name: ArtifactName, value: dict[str, Any]) -> None:
        sections[name.value] = {**value, "legacy": True}
        carried.add(name)

    if _file(folder, ArtifactName.INPUT_AUDIO).is_file():
        placeholder(ArtifactName.IMPORT_REQUEST, {"source_path": None, "clean_audio": None})
    if ArtifactName.NAME_CORRECTED_TRANSCRIPT in current:
        placeholder(ArtifactName.NAME_CORRECTION_SUGGESTIONS, {"suggestions": []})
        placeholder(ArtifactName.NAME_CORRECTION_DECISIONS, {"corrections": []})
    for name in _FOLDED:
        path = _file(folder, name)
        if not path.is_file():
            continue
        value = _read_json(path)
        # An unreadable file still counted as done; its placeholder keeps that work complete.
        sections[name.value] = value if isinstance(value, dict) else {"legacy": True, "unreadable": True}
        if name in current:
            carried.add(name)
    if ArtifactName.EXTRACTED_GLOSSARY_TERMS in carried:
        entries = sections[ArtifactName.EXTRACTED_GLOSSARY_TERMS.value].get("entries", [])
        placeholder(ArtifactName.GLOSSARY_SUGGESTIONS, {"proposals": []})
        placeholder(ArtifactName.GLOSSARY_DECISIONS, {"entries": entries})
    if ArtifactName.SPELLCHECKED_TRANSCRIPT in current:
        placeholder(ArtifactName.SPELLING_SUGGESTIONS, {"suggestions": []})
        placeholder(ArtifactName.SPELLING_DECISIONS, {"corrections": []})
    reviewed_path = _file(folder, ArtifactName.REVIEWED_TRANSCRIPT)
    spellchecked_path = _file(folder, ArtifactName.SPELLCHECKED_TRANSCRIPT)
    if reviewed_path.is_file() and spellchecked_path.is_file():
        try:
            edits: dict[str, Any] = transcript_edits.diff(Transcript.load(spellchecked_path), Transcript.load(reviewed_path)).model_dump(
                mode="json"
            )
        except (OSError, ValueError, ValidationError):
            edits = {"edits": [], "unreadable": True}
        sections[ArtifactName.TRANSCRIPT_REVIEW_EDITS.value] = {**edits, "legacy": True}
        if ArtifactName.REVIEWED_TRANSCRIPT in current:
            carried.add(ArtifactName.TRANSCRIPT_REVIEW_EDITS)
    if ArtifactName.REVIEWED_TRANSCRIPT in current:
        placeholder(ArtifactName.VOICE_PRINT_DECISION, {"accepted": None})
        placeholder(ArtifactName.VOICE_PRINT_ENHANCEMENT, {"enhanced_player_count": 0, "clip_count": 0})
    return sections, carried


def move_retired_files(folder: Path) -> list[str]:
    """Move the files the sections replaced (and the old review draft) into `legacy/`; return their names."""
    moved: list[str] = []
    names = [ARTIFACTS[name].filename for name in _FOLDED] + [REVIEW_DRAFT_FILENAME]
    for filename in names:
        source = folder / filename
        if source.is_file():
            target = folder / LEGACY_DIRNAME / filename
            target.parent.mkdir(exist_ok=True)
            shutil.move(source, target)
            moved.append(filename)
    return moved
