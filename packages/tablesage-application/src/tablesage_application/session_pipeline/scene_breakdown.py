"""Scene records generated alongside the Ledger, retaining their generation-time provenance."""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from ..paths import ARTIFACTS, LEDGER_PAIR_MARKER, ArtifactName

if TYPE_CHECKING:
    from .generate_ledger import Ledger

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LedgerRange(_StrictModel):
    start_index: int = Field(ge=0, strict=True, description="Inclusive zero-based index in ledger.utterances.")
    end_index: int = Field(ge=0, strict=True, description="Inclusive zero-based index in ledger.utterances.")

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end_index < self.start_index:
            raise ValueError("Ledger range endpoints are reversed.")
        return self


class Scene(_StrictModel):
    title: Text
    location: Text | None = Field(description="A recognizable source-supported location; null when unknown.")
    participants: list[Text]
    situation: Text
    outcome: Text
    carry_forward: list[Text]
    signature_detail: Text | None = Field(description="One supported sensory, thematic, or personal cue; null if none is useful.")
    ledger_ranges: list[LedgerRange] = Field(min_length=1)


class SceneBreakdownContent(_StrictModel):
    ending_situation: Text
    scenes: list[Scene]

    def validate_coverage(self, utterance_count: int) -> None:
        """Partition the Ledger exactly once, without allocating memory for untrusted endpoints."""
        intervals: list[tuple[int, int]] = []
        previous_start = -1
        for scene_index, scene in enumerate(self.scenes):
            starts = [span.start_index for span in scene.ledger_ranges]
            if starts != sorted(starts):
                raise ValueError(f"Scene {scene_index} Ledger ranges must be ordered by start index: {starts}.")
            if starts[0] <= previous_start:
                raise ValueError(
                    f"Scenes must be ordered by their first Ledger entry: scene {scene_index} starts at {starts[0]} after {previous_start}."
                )
            previous_start = starts[0]
            for span in scene.ledger_ranges:
                if span.end_index >= utterance_count:
                    raise ValueError(
                        f"Scene {scene_index} Ledger range {span.start_index}..{span.end_index} is out of bounds: "
                        f"the Ledger has {utterance_count} entries, valid indices 0..{utterance_count - 1}."
                    )
                intervals.append((span.start_index, span.end_index))
        cursor = 0
        for start, end in sorted(intervals):
            if start != cursor:
                raise ValueError(
                    f"Scene Ledger ranges must cover every entry exactly once: expected next index {cursor}, got range {start}..{end}."
                )
            cursor = end + 1
        if cursor != utterance_count:
            raise ValueError(
                f"Scene Ledger ranges stop at {cursor - 1}, but must cover all {utterance_count} entries through {utterance_count - 1}."
            )


class SceneBreakdown(SceneBreakdownContent):
    version: Literal[1] = 1
    session_id: uuid.UUID
    session_name: Text
    starting_situation: Text
    ledger_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_internal_ranges(self) -> Self:
        # Offline readers can verify a contiguous partition; the paired loader additionally
        # verifies its final endpoint against the actual Ledger length.
        last_index = max((span.end_index for scene in self.scenes for span in scene.ledger_ranges), default=-1)
        self.validate_coverage(last_index + 1)
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))


def load_current_scene_breakdown(session_folder: Path) -> SceneBreakdown:
    if (session_folder / LEDGER_PAIR_MARKER).exists():
        raise ValueError("Ledger replacement was interrupted; regenerate the Ledger and Scene Breakdown together.")
    breakdown = SceneBreakdown.load(session_folder / ARTIFACTS[ArtifactName.SCENE_BREAKDOWN].filename)
    return breakdown


def persist_ledger_pair(ledger: Ledger, content: SceneBreakdownContent, session_folder: Path) -> SceneBreakdown:
    """Replace the paired canonical outputs and Ledger rendering as one rollback unit.

    Handled write failures restore the old files. A process interruption leaves a marker so
    readers refuse a potentially mixed pair until regeneration succeeds.
    """
    content.validate_coverage(len(ledger.utterances))
    ledger_bytes = (ledger.model_dump_json(indent=2) + "\n").encode("utf-8")
    breakdown = SceneBreakdown(
        session_id=ledger.session_id,
        session_name=ledger.session_name,
        starting_situation=ledger.starting_situation,
        ledger_sha256=hashlib.sha256(ledger_bytes).hexdigest(),
        **content.model_dump(),
    )
    updates: dict[str, bytes | None] = {
        ARTIFACTS[ArtifactName.LEDGER].filename: ledger_bytes,
        "ledger.md": ledger.to_markdown().encode("utf-8"),
        ARTIFACTS[ArtifactName.SCENE_BREAKDOWN].filename: (breakdown.model_dump_json(indent=2) + "\n").encode("utf-8"),
    }
    originals = {name: (session_folder / name).read_bytes() if (session_folder / name).exists() else None for name in updates}
    marker = session_folder / LEDGER_PAIR_MARKER
    old_marker = marker.read_bytes() if marker.exists() else None
    with TemporaryDirectory(prefix=".ledger-pair-", dir=session_folder) as staging:
        stage = Path(staging)
        for name, data in updates.items():
            if data is not None:
                (stage / name).write_bytes(data)
        marker.write_text("Ledger pair replacement in progress; regenerate if interrupted.\n", encoding="utf-8")
        changed: list[str] = []
        try:
            for name, data in updates.items():
                target = session_folder / name
                # Track before mutation so an interrupt immediately after rename/unlink also
                # restores this target. Restoring an unchanged target is harmless.
                changed.append(name)
                if data is None:
                    target.unlink(missing_ok=True)
                else:
                    (stage / name).replace(target)
            marker.unlink()
        except BaseException:
            # Leave the marker present if rollback itself fails.
            if not marker.exists():
                marker.write_text("Ledger pair rollback in progress.\n", encoding="utf-8")
            for name in reversed(changed):
                old = originals[name]
                target = session_folder / name
                if old is None:
                    target.unlink(missing_ok=True)
                else:
                    restore = stage / name
                    restore.write_bytes(old)
                    os.replace(restore, target)
            if old_marker is None:
                marker.unlink(missing_ok=True)
            else:
                marker.write_bytes(old_marker)
            raise
    return breakdown
