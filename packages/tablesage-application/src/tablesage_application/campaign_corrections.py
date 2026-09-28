"""The campaign's current, portable set of approved spelling corrections."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .paths import ArtifactName
from .session_pipeline import processing_state
from .session_pipeline.atomic_files import atomic_write

FILENAME = "approved_corrections.json"
_locks: dict[Path, threading.Lock] = {}
_locks_guard = threading.Lock()


@dataclass(frozen=True)
class Mapping:
    from_text: str
    to_text: str
    case_sensitive: bool

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> Mapping:
        return cls(str(value["from_text"]), str(value["to_text"]), bool(value.get("case_sensitive", False)))

    def as_dict(self) -> dict[str, object]:
        return {"from_text": self.from_text, "to_text": self.to_text, "case_sensitive": self.case_sensitive}


def _lock_for(folder: Path) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(folder.resolve(), threading.Lock())


def _read_or_seed(folder: Path, session_folders: Iterable[Path]) -> set[Mapping]:
    target = folder / FILENAME
    if target.is_file():
        data = json.loads(target.read_text(encoding="utf-8"))
        return {Mapping.from_dict(row) for row in data["mappings"]}

    mappings: set[Mapping] = set()
    for session_folder in session_folders:
        section = processing_state.load(session_folder).sections.get(ArtifactName.SPELLING_DECISIONS.value)
        if not isinstance(section, dict):
            continue
        for row in section.get("rows", section.get("corrections", [])):
            if not row.get("removed", False):
                mappings.add(Mapping.from_dict(row))
    _write(folder, mappings)
    return mappings


def _write(folder: Path, mappings: set[Mapping]) -> None:
    ordered = sorted(mappings, key=lambda item: (item.from_text.casefold(), item.from_text, item.to_text, item.case_sensitive))
    data = json.dumps({"version": 1, "mappings": [item.as_dict() for item in ordered]}, indent=2) + "\n"
    atomic_write(folder / FILENAME, data.encode("utf-8"))


def load(folder: Path, session_folders: Iterable[Path]) -> set[Mapping]:
    with _lock_for(folder):
        return _read_or_seed(folder, session_folders)


def change(folder: Path, session_folders: Iterable[Path], *, add: Iterable[Mapping] = (), remove: Iterable[Mapping] = ()) -> None:
    with _lock_for(folder):
        mappings = _read_or_seed(folder, session_folders)
        original = set(mappings)
        mappings.difference_update(remove)
        mappings.update(add)
        if mappings != original:
            _write(folder, mappings)
