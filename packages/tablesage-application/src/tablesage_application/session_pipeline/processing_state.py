"""A Session's processing state document, `processing_state.json`.

One current-state document per Session folder (see the processing-step-architecture work item). It holds:

- `records`: one completion record per build step, keyed by the step's artifact name. A record lists the
  content fingerprint of every input the step declared when it completed; the artifact graph compares
  those against the inputs as they are now to decide staleness.
- `sections`: results that are not documents -- decisions, suggestions, receipts -- keyed by artifact name.
- `drafts`: uncompleted work a manual step saved on Cancel, keyed by step id.
- `failures`: each processing step's last failure, informational only; completion never reads it.

Every change goes through `update`, a locked read-modify-write that writes atomically, keeps the previous
version as `processing_state.json.bak`, and logs one wide event -- the app log is this document's history.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import widelog
from pydantic import BaseModel, Field, ValidationError

from ..paths import ARTIFACTS
from .atomic_files import atomic_write

STATE_FILENAME = "processing_state.json"
BACKUP_FILENAME = "processing_state.json.bak"
SCHEMA_VERSION = 1
# Values up to this size are logged whole on each write; larger ones are logged by fingerprint only.
_LOGGED_VALUE_LIMIT = 2_000


class InputFingerprint(BaseModel):
    """An input's content at completion time. Files also carry the size and mtime they had when hashed, so an
    unchanged file is recognised without re-hashing; a section (or anything that is not a file) leaves them None."""

    sha256: str
    size: int | None = None
    mtime_ns: int | None = None


class CompletionRecord(BaseModel):
    complete: bool = True
    completed_at: datetime
    inputs: dict[str, InputFingerprint] = Field(default_factory=dict)


class StepFailure(BaseModel):
    message: str
    at: datetime
    run_id: str | None = None


class ProcessingState(BaseModel):
    version: int = SCHEMA_VERSION
    # Set once a Session processed before this document existed has been imported (see `needs_legacy_import`).
    legacy_imported_at: datetime | None = None
    records: dict[str, CompletionRecord] = Field(default_factory=dict)
    sections: dict[str, Any] = Field(default_factory=dict)
    drafts: dict[str, Any] = Field(default_factory=dict)
    failures: dict[str, StepFailure] = Field(default_factory=dict)


def state_path(session_folder: Path) -> Path:
    return session_folder / STATE_FILENAME


def backup_path(session_folder: Path) -> Path:
    return session_folder / BACKUP_FILENAME


def exists(session_folder: Path) -> bool:
    return state_path(session_folder).is_file()


def needs_legacy_import(session_folder: Path) -> bool:
    """Whether the folder holds artifacts from before this document existed and hasn't been imported yet."""
    if exists(session_folder) or not session_folder.is_dir():
        return False
    return any(spec.filename and (session_folder / spec.filename).is_file() for spec in ARTIFACTS.values())


def _read(path: Path) -> ProcessingState:
    return ProcessingState.model_validate_json(path.read_bytes())


def load(session_folder: Path) -> ProcessingState:
    """The folder's state; empty when there is none. An unreadable document falls back to its backup, and an
    unreadable backup to an empty state -- both logged, since everything then reads as incomplete."""
    path = state_path(session_folder)
    if not path.is_file():
        return ProcessingState()
    try:
        return _read(path)
    except (OSError, ValidationError, ValueError) as exc:
        with widelog.wide_event(op="processing_state.unreadable", session_folder=str(session_folder), error=str(exc)) as log:
            try:
                state = _read(backup_path(session_folder))
            except (OSError, ValidationError, ValueError) as backup_exc:
                log.set(recovered_from="none", backup_error=str(backup_exc))
                return ProcessingState()
            log.set(recovered_from="backup")
            return state


_locks: dict[Path, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(session_folder: Path) -> threading.Lock:
    key = session_folder.resolve()
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def _logged_value(value: object) -> object:
    if value is None:
        return None
    encoded = _canonical_json(value)
    return value if len(encoded) <= _LOGGED_VALUE_LIMIT else {"sha256": _sha256_bytes(encoded), "bytes": len(encoded)}


def _changes(before: ProcessingState, after: ProcessingState) -> dict[str, object]:
    """What a write changed, for its wide event: each changed key's old and new value (or fingerprint)."""
    changed: dict[str, object] = {}
    if before.legacy_imported_at != after.legacy_imported_at:
        changed["legacy_imported_at"] = {"old": before.legacy_imported_at, "new": after.legacy_imported_at}
    for part in ("records", "sections", "drafts", "failures"):
        old: dict[str, Any] = before.model_dump(mode="json")[part]
        new: dict[str, Any] = after.model_dump(mode="json")[part]
        for key in sorted(set(old) | set(new)):
            if old.get(key) != new.get(key):
                changed[f"{part}.{key}"] = {"old": _logged_value(old.get(key)), "new": _logged_value(new.get(key))}
    return changed


def update(session_folder: Path, mutate: Callable[[ProcessingState], None], *, reason: str) -> ProcessingState:
    """Apply `mutate` to the current state and save it, as one locked read-modify-write; return the new state.

    The previous document is kept as the backup. Nothing is written when `mutate` changes nothing.
    """
    with _lock_for(session_folder):
        before = load(session_folder)
        after = before.model_copy(deep=True)
        mutate(after)
        changes = _changes(before, after)
        if not changes:
            return after
        with widelog.wide_event(op="processing_state.write", session_folder=str(session_folder), reason=reason, changes=changes):
            path = state_path(session_folder)
            if path.is_file():
                atomic_write(backup_path(session_folder), path.read_bytes())
            atomic_write(path, after.model_dump_json(indent=2).encode("utf-8") + b"\n")
        return after


def delete(session_folder: Path) -> None:
    """Remove the document and its backup (Clean Session)."""
    with _lock_for(session_folder):
        state_path(session_folder).unlink(missing_ok=True)
        backup_path(session_folder).unlink(missing_ok=True)


def now() -> datetime:
    return datetime.now(UTC)


# Fingerprints


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def value_fingerprint(value: object) -> InputFingerprint:
    """A section's (or any JSON value's) fingerprint: the hash of its canonical JSON."""
    return InputFingerprint(sha256=_sha256_bytes(_canonical_json(value)))


# Hashes of files already read this process, by (path, size, mtime) -- a changed file gets a new key.
_hash_cache: dict[tuple[Path, int, int], str] = {}
_hash_cache_guard = threading.Lock()


def _hash_file(path: Path, size: int, mtime_ns: int) -> str:
    key = (path, size, mtime_ns)
    with _hash_cache_guard:
        cached = _hash_cache.get(key)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    value = digest.hexdigest()
    with _hash_cache_guard:
        _hash_cache[key] = value
    return value


def file_fingerprint(path: Path) -> InputFingerprint | None:
    """The file's current fingerprint, or None when it doesn't exist."""
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    return InputFingerprint(sha256=_hash_file(path, stat.st_size, stat.st_mtime_ns), size=stat.st_size, mtime_ns=stat.st_mtime_ns)


def file_matches(path: Path, recorded: InputFingerprint) -> bool:
    """Whether the file still has the recorded content. An unchanged size and mtime is trusted without hashing;
    otherwise (say, after a copy reset the mtime) the file is hashed and compared."""
    try:
        stat = path.stat()
    except FileNotFoundError:
        return False
    if (stat.st_size, stat.st_mtime_ns) == (recorded.size, recorded.mtime_ns):
        return True
    return _hash_file(path, stat.st_size, stat.st_mtime_ns) == recorded.sha256
