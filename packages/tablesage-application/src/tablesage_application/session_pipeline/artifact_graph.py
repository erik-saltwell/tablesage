from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ..paths import ARTIFACTS, ArtifactName


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
        return self.session_folder / ARTIFACTS[self.name].filename


@dataclass(frozen=True)
class FileRef:
    """A physical output that participates in a step but is not a logical artifact."""

    path: Path


@dataclass(frozen=True)
class TimestampInput:
    modified_ns: int


@dataclass(frozen=True)
class SystemPromptInput:
    """A packaged LLM system prompt whose modification time affects generated outputs."""

    path: Path


Dependency = ArtifactRef | TimestampInput | SystemPromptInput


@dataclass(frozen=True)
class BuildStep:
    name: ArtifactName
    outputs: tuple[ArtifactRef | FileRef, ...]
    dependencies: tuple[Dependency, ...]


@dataclass(frozen=True)
class GenerationTask:
    session_id: uuid.UUID
    artifact_name: ArtifactName


class ArtifactGraph:
    """Evaluate artifact freshness recursively across files, logical clocks, and Sessions."""

    def __init__(self, steps: tuple[BuildStep, ...], *, interrupted: frozenset[ArtifactRef] = frozenset()) -> None:
        self.steps = steps
        self._step_by_output = {output: step for step in steps for output in step.outputs if isinstance(output, ArtifactRef)}
        self._interrupted = interrupted
        self._cache: dict[ArtifactRef, ArtifactStatus] = {}
        self._visiting: set[ArtifactRef] = set()

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

    def _evaluate(self, artifact: ArtifactRef) -> ArtifactStatus:
        exists = artifact.path.is_file()
        if not exists:
            return ArtifactStatus.MISSING
        if artifact in self._interrupted:
            return ArtifactStatus.STALE

        step = self._step_by_output.get(artifact)
        if step is None:
            return ArtifactStatus.CURRENT

        if any(not output.path.is_file() for output in step.outputs):
            return ArtifactStatus.STALE

        newest_dependency_ns = 0
        for dependency in step.dependencies:
            if isinstance(dependency, TimestampInput):
                newest_dependency_ns = max(newest_dependency_ns, dependency.modified_ns)
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

    def session_statuses(self, session_folder: Path) -> dict[ArtifactName, ArtifactStatus]:
        return {name: self.status(ArtifactRef(session_folder, name)) for name in ARTIFACTS}

    def step_for(self, artifact: ArtifactRef) -> BuildStep | None:
        return self._step_by_output.get(artifact)


GENERATION_ORDER: tuple[ArtifactName, ...] = (
    ArtifactName.ROLE_TRANSCRIPT,
    ArtifactName.TRANSCRIPT_SECTIONS,
    ArtifactName.LEDGER,
    ArtifactName.PLAYER_INTRODUCTIONS,
    ArtifactName.RECAP_SUMMARY,
    ArtifactName.SUMMARY,
)

GENERATION_LABELS: dict[ArtifactName, str] = {
    ArtifactName.ROLE_TRANSCRIPT: "Role Transcript",
    ArtifactName.TRANSCRIPT_SECTIONS: "Transcript Sections",
    ArtifactName.LEDGER: "Ledger + Scene Breakdown",
    ArtifactName.PLAYER_INTRODUCTIONS: "Player Introductions",
    ArtifactName.RECAP_SUMMARY: "Recap Summary",
    ArtifactName.SUMMARY: "Summary",
}

GENERATION_DEPENDENCIES: dict[ArtifactName, frozenset[ArtifactName]] = {
    ArtifactName.ROLE_TRANSCRIPT: frozenset(),
    ArtifactName.TRANSCRIPT_SECTIONS: frozenset({ArtifactName.ROLE_TRANSCRIPT}),
    ArtifactName.LEDGER: frozenset({ArtifactName.ROLE_TRANSCRIPT, ArtifactName.TRANSCRIPT_SECTIONS}),
    ArtifactName.PLAYER_INTRODUCTIONS: frozenset({ArtifactName.ROLE_TRANSCRIPT, ArtifactName.TRANSCRIPT_SECTIONS}),
    ArtifactName.RECAP_SUMMARY: frozenset({ArtifactName.LEDGER}),
    ArtifactName.SUMMARY: frozenset({ArtifactName.LEDGER, ArtifactName.PLAYER_INTRODUCTIONS}),
}
