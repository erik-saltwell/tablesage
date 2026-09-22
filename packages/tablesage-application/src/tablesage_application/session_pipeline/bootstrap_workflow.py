"""Typed, atomic working-state documents for new-speaker bootstrap processing."""

from __future__ import annotations

import hashlib
import os
import tempfile
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

WORKFLOW_DIRECTORY = "processing"
MANIFEST_FILENAME = "bootstrap-manifest.json"
MANIFEST_SCHEMA_VERSION = 1


class BootstrapDocumentName(StrEnum):
    DIARIZED = "diarized"
    EVIDENCE = "bootstrap-evidence"
    SELECTION = "bootstrap-selection"
    REVIEW = "bootstrap-review"
    IDENTIFICATION = "identification"
    NEW_SPEAKER_REVIEW = "new-speaker-review"
    SPELLING_REVIEW = "spelling-review"


class BootstrapDocumentStatus(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"
    SKIPPED = "skipped"


class SourceUtteranceId(BaseModel, frozen=True):
    """Stable identity for a raw diarized utterance within one bootstrap run."""

    run_id: uuid.UUID
    original_index: int = Field(ge=0)

    @property
    def value(self) -> str:
        return f"{self.run_id}:{self.original_index}"


class SourceClipId(BaseModel, frozen=True):
    """Stable subclip identity; bounds are retained independently from transcript row order."""

    utterance_id: SourceUtteranceId
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)


class BootstrapAttendeeSnapshot(BaseModel, frozen=True):
    player_id: uuid.UUID
    player_name: str
    roles: tuple[str, ...]
    usable_centroid: bool


class BootstrapReferenceSnapshot(BaseModel, frozen=True):
    player_id: uuid.UUID
    player_name: str
    embedding: tuple[float, ...]
    embedding_dimension: int
    provenance: str


class BootstrapEligibility(BaseModel, frozen=True):
    attendees: tuple[BootstrapAttendeeSnapshot, ...]
    targets: tuple[uuid.UUID, ...]
    references: tuple[BootstrapReferenceSnapshot, ...]


class BootstrapDocumentRecord(BaseModel, frozen=True):
    status: BootstrapDocumentStatus = BootstrapDocumentStatus.PENDING
    sha256: str | None = None
    revision: int = Field(default=0, ge=0)


class BootstrapWorkflowManifest(BaseModel):
    schema_version: int = Field(default=MANIFEST_SCHEMA_VERSION, ge=1)
    run_id: uuid.UUID
    source_sha256: str
    revision: int = Field(default=0, ge=0)
    documents: dict[BootstrapDocumentName, BootstrapDocumentRecord] = Field(
        default_factory=lambda: {name: BootstrapDocumentRecord() for name in BootstrapDocumentName}
    )
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def processing_folder(session_folder: Path) -> Path:
    return session_folder / WORKFLOW_DIRECTORY


def manifest_path(session_folder: Path) -> Path:
    return processing_folder(session_folder) / MANIFEST_FILENAME


def document_path(session_folder: Path, name: BootstrapDocumentName) -> Path:
    return processing_folder(session_folder) / f"{name.value}.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_document(session_folder: Path, name: BootstrapDocumentName, payload: BaseModel) -> BootstrapDocumentRecord:
    """Atomically write a workflow document and return the manifest record to publish next."""
    data = payload.model_dump_json(indent=2).encode("utf-8") + b"\n"
    _atomic_write(document_path(session_folder, name), data)
    return BootstrapDocumentRecord(status=BootstrapDocumentStatus.COMPLETE, sha256=sha256_bytes(data), revision=1)


def write_manifest(session_folder: Path, manifest: BootstrapWorkflowManifest) -> str:
    """Atomically publish a manifest after all documents referenced by it exist."""
    manifest.updated_at = datetime.now(UTC)
    data = manifest.model_dump_json(indent=2).encode("utf-8") + b"\n"
    _atomic_write(manifest_path(session_folder), data)
    return sha256_bytes(data)


def atomic_write(path: Path, data: bytes) -> None:
    """Publish a small workflow-adjacent file with the same durability rules as manifests."""
    _atomic_write(path, data)


def record_document(
    manifest: BootstrapWorkflowManifest, name: BootstrapDocumentName, record: BootstrapDocumentRecord
) -> BootstrapWorkflowManifest:
    """Return the next manifest revision after a document has been safely written."""
    revision = manifest.revision + 1
    documents = dict(manifest.documents)
    documents[name] = record.model_copy(update={"revision": revision})
    return manifest.model_copy(update={"revision": revision, "documents": documents})


def load_manifest(session_folder: Path) -> BootstrapWorkflowManifest | None:
    path = manifest_path(session_folder)
    if not path.is_file():
        return None
    return BootstrapWorkflowManifest.model_validate_json(path.read_text(encoding="utf-8"))


def manifest_matches(manifest: BootstrapWorkflowManifest | None, run_id: uuid.UUID, source_sha256: str) -> bool:
    """Whether a manifest can safely resume a particular run/source pair."""
    return manifest is not None and manifest.run_id == run_id and manifest.source_sha256 == source_sha256


def document_status(manifest: BootstrapWorkflowManifest, name: BootstrapDocumentName) -> BootstrapDocumentStatus:
    """Return a checkpoint status without treating an unreferenced file as completed."""
    return manifest.documents.get(name, BootstrapDocumentRecord()).status


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
