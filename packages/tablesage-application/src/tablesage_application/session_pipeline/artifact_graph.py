from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ..paths import ARTIFACTS, ArtifactName
from . import processing_state
from .bundles.campaign_matters import SECTIONS


class ArtifactStatus(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    MISSING = "missing"


@dataclass(frozen=True)
class ArtifactRef:
    session_folder: Path
    name: ArtifactName

    @property
    def path(self) -> Path:
        """The artifact's file -- for a section, the legacy file it was imported from."""
        filename = ARTIFACTS[self.name].filename
        if not filename:
            raise ValueError(f"{self.name.value} is a processing-state section and has no file.")
        return self.session_folder / filename

    @property
    def is_section(self) -> bool:
        return not ARTIFACTS[self.name].is_file


@dataclass(frozen=True)
class FileRef:
    """A physical output that participates in a step but is not a logical artifact."""

    path: Path


@dataclass(frozen=True)
class SystemPromptInput:
    """A packaged prompt, template or schema whose content affects generated outputs."""

    path: Path


@dataclass(frozen=True)
class ValueInput:
    key: str
    value: object


Dependency = ArtifactRef | SystemPromptInput | ValueInput


@dataclass(frozen=True)
class BuildStep:
    name: ArtifactName
    outputs: tuple[ArtifactRef | FileRef, ...]
    dependencies: tuple[Dependency, ...]

    @property
    def folder(self) -> Path:
        """The Session folder that owns this step's outputs, and so its completion record."""
        return next(output.session_folder for output in self.outputs if isinstance(output, ArtifactRef))


@dataclass(frozen=True)
class GenerationTask:
    session_id: uuid.UUID
    artifact_name: ArtifactName


def dependency_key(owner_folder: Path, dependency: Dependency) -> str:
    """How a completion record names an input. Keys never hold absolute paths, so a copied or moved campaign
    keeps matching: an artifact in another Session of the campaign is named by its sibling folder."""
    if isinstance(dependency, ValueInput):
        return f"value:{dependency.key}"
    if isinstance(dependency, SystemPromptInput):
        suffix = "" if dependency.path.name == "system.md" else f"/{dependency.path.name}"
        return f"prompt:{dependency.path.parent.name}{suffix}"
    if dependency.session_folder == owner_folder:
        return f"artifact:{dependency.name.value}"
    return f"artifact:{dependency.session_folder.name}/{dependency.name.value}"


StateLoader = Callable[[Path], processing_state.ProcessingState]


def _fingerprint(dependency: Dependency, states: StateLoader) -> processing_state.InputFingerprint | None:
    """A dependency's current fingerprint, or None when it doesn't exist."""
    if isinstance(dependency, ValueInput):
        return processing_state.value_fingerprint(dependency.value)
    if isinstance(dependency, ArtifactRef) and dependency.is_section:
        sections = states(dependency.session_folder).sections
        return processing_state.value_fingerprint(sections[dependency.name.value]) if dependency.name.value in sections else None
    return processing_state.file_fingerprint(dependency.path)


def _matches(dependency: Dependency, recorded: processing_state.InputFingerprint, states: StateLoader) -> bool:
    if isinstance(dependency, ValueInput):
        return processing_state.value_fingerprint(dependency.value).sha256 == recorded.sha256
    if isinstance(dependency, ArtifactRef) and dependency.is_section:
        current = _fingerprint(dependency, states)
        return current is not None and current.sha256 == recorded.sha256
    return processing_state.file_matches(dependency.path, recorded)


def current_fingerprints(step: BuildStep, states: StateLoader = processing_state.load) -> dict[str, processing_state.InputFingerprint]:
    """The fingerprints a completion record for `step` stores: each declared input as it is now. An input that
    doesn't exist is left out, so the record reads as stale until the step runs again with it present."""
    fingerprints: dict[str, processing_state.InputFingerprint] = {}
    for dependency in step.dependencies:
        fingerprint = _fingerprint(dependency, states)
        if fingerprint is not None:
            fingerprints[dependency_key(step.folder, dependency)] = fingerprint
    return fingerprints


class ArtifactGraph:
    """Evaluate artifact freshness recursively across Sessions from content-fingerprinted completion records.

    An output is current when its file exists, its step's record says complete, every input the step declares
    is itself current and was recorded, and each recorded fingerprint still matches that input's content. An
    input the step no longer declares is ignored; one it declares but never recorded makes the output stale.
    """

    def __init__(self, steps: tuple[BuildStep, ...], *, interrupted: frozenset[ArtifactRef] = frozenset()) -> None:
        self.steps = steps
        self._step_by_output = {output: step for step in steps for output in step.outputs if isinstance(output, ArtifactRef)}
        self._interrupted = interrupted
        self._cache: dict[ArtifactRef, ArtifactStatus] = {}
        self._visiting: set[ArtifactRef] = set()
        self._states: dict[Path, processing_state.ProcessingState] = {}

    def state(self, session_folder: Path) -> processing_state.ProcessingState:
        state = self._states.get(session_folder)
        if state is None:
            state = self._states[session_folder] = processing_state.load(session_folder)
        return state

    def status(self, artifact: ArtifactRef) -> ArtifactStatus:
        cached = self._cache.get(artifact)
        if cached is not None:
            return cached
        if artifact in self._visiting:
            raise ValueError(f"Artifact dependency cycle at {artifact.name.value}.")

        self._visiting.add(artifact)
        try:
            status = self._evaluate(artifact)
            self._cache[artifact] = status
            return status
        finally:
            self._visiting.remove(artifact)

    def exists(self, output: ArtifactRef | FileRef) -> bool:
        if isinstance(output, ArtifactRef) and output.is_section:
            return output.name.value in self.state(output.session_folder).sections
        return output.path.is_file()

    def _evaluate(self, artifact: ArtifactRef) -> ArtifactStatus:
        if not self.exists(artifact):
            return ArtifactStatus.MISSING
        if artifact in self._interrupted:
            return ArtifactStatus.STALE
        if artifact.name is ArtifactName.REVIEWED_TRANSCRIPT:
            checkpoint = self.state(artifact.session_folder).reviewed_transcript_checkpoint
            if checkpoint is not None:
                # Hash the actual bytes: adoption does not pretend historical machine inputs are current.
                fingerprint = processing_state.file_fingerprint(artifact.path)
                return (
                    ArtifactStatus.CURRENT if fingerprint is not None and fingerprint.sha256 == checkpoint.sha256 else ArtifactStatus.STALE
                )
        step = self.step_for(artifact)
        if step is None:
            return ArtifactStatus.CURRENT
        if any(not self.exists(output) for output in step.outputs):
            return ArtifactStatus.STALE

        record = self.state(step.folder).records.get(step.name.value)
        if record is None or not record.complete:
            return ArtifactStatus.STALE
        for dependency in step.dependencies:
            recorded = record.inputs.get(dependency_key(step.folder, dependency))
            if recorded is None:
                return ArtifactStatus.STALE
            if isinstance(dependency, ArtifactRef) and self.status(dependency) is not ArtifactStatus.CURRENT:
                return ArtifactStatus.STALE
            if not _matches(dependency, recorded, self.state):
                return ArtifactStatus.STALE
        return ArtifactStatus.CURRENT

    def session_statuses(self, session_folder: Path) -> dict[ArtifactName, ArtifactStatus]:
        return {name: self.status(ArtifactRef(session_folder, name)) for name in ARTIFACTS}

    def step_for(self, artifact: ArtifactRef) -> BuildStep | None:
        return self._step_by_output.get(artifact)


class LegacyArtifactGraph(ArtifactGraph):
    """The retired modification-time evaluator, kept only to import existing Sessions once (see
    `Application._migrate_legacy_sessions`): an output is current when it is newer than every dependency."""

    def exists(self, output: ArtifactRef | FileRef) -> bool:
        return isinstance(output, FileRef) or bool(ARTIFACTS[output.name].filename) and output.path.is_file()

    def _evaluate(self, artifact: ArtifactRef) -> ArtifactStatus:
        if not self.exists(artifact):
            return ArtifactStatus.MISSING
        if artifact in self._interrupted:
            return ArtifactStatus.STALE
        step = self.step_for(artifact)
        if step is None:
            return ArtifactStatus.CURRENT
        if any(not (output.path.is_file() if isinstance(output, FileRef) else self.exists(output)) for output in step.outputs):
            return ArtifactStatus.STALE

        newest_dependency_ns = 0
        for dependency in step.dependencies:
            if isinstance(dependency, ValueInput):
                continue
            if isinstance(dependency, SystemPromptInput):
                if not dependency.path.is_file():
                    return ArtifactStatus.STALE
                newest_dependency_ns = max(newest_dependency_ns, dependency.path.stat().st_mtime_ns)
                continue
            if self.status(dependency) is not ArtifactStatus.CURRENT:
                return ArtifactStatus.STALE
            newest_dependency_ns = max(newest_dependency_ns, dependency.path.stat().st_mtime_ns)

        oldest_output_ns = min(output.path.stat().st_mtime_ns for output in step.outputs)
        return ArtifactStatus.STALE if newest_dependency_ns > oldest_output_ns else ArtifactStatus.CURRENT


GENERATION_ORDER: tuple[ArtifactName, ...] = (
    ArtifactName.ROLE_TRANSCRIPT,
    ArtifactName.TRANSCRIPT_SECTIONS,
    ArtifactName.LEDGER,
    ArtifactName.SCENE_LOG,
    *(ArtifactName(section) for section in SECTIONS),
    ArtifactName.POST_SESSION_MATTERS,
    ArtifactName.SUMMARY,
    ArtifactName.TABLE_RECAP,
)

DEFERRED_GENERATION = frozenset({ArtifactName.RECAP_SUMMARY})
REGENERATABLE = frozenset((*GENERATION_ORDER, ArtifactName.PLAYER_INTRODUCTIONS))
MODEL_GENERATED_ARTIFACTS = REGENERATABLE - {ArtifactName.ROLE_TRANSCRIPT, ArtifactName.POST_SESSION_MATTERS, ArtifactName.SUMMARY}
# Hidden producers are never selectable.
REGENERATION_CHOICES = tuple(name for name in (*GENERATION_ORDER, ArtifactName.PLAYER_INTRODUCTIONS) if ARTIFACTS[name].should_show_in_ui)
GENERATION_LABELS: dict[ArtifactName, str] = {name: spec.display_name for name, spec in ARTIFACTS.items()}
