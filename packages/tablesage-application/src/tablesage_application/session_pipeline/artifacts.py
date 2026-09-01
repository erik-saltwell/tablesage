from __future__ import annotations

import shutil
from enum import Enum
from pathlib import Path

import widelog

from ..paths import ARTIFACTS, ArtifactCategory, ArtifactName


def session_artifacts(session_folder: Path) -> dict[ArtifactName, bool]:
    """What exists on disk for a session -- drives the indicator panel and the P/G/T gates."""
    return {name: (session_folder / spec.filename).is_file() for name, spec in ARTIFACTS.items()}


def invalidate_category(session_folder: Path, category: ArtifactCategory) -> None:
    """Delete every existing session artifact in *category*."""
    with widelog.wide_event(op="invalidate_artifact_category", session_folder=str(session_folder), category=category.value):
        for spec in ARTIFACTS.values():
            if spec.category is category:
                (session_folder / spec.filename).unlink(missing_ok=True)


def delete_transcript_and_dependents(session_folder: Path) -> None:
    """Delete the machine transcript and everything derived from it.

    Deletes every category except `IMPORTED` -- `FROM_AUDIO` (the transcript itself),
    `FROM_TRANSCRIPT` (Reviewed Transcript, Role Transcript, benchmark, Ledger), and `FROM_LOG`
    (Summary). The raw input audio is untouched.
    """
    with widelog.wide_event(op="delete_transcript_and_dependents", session_folder=str(session_folder)):
        for category in (ArtifactCategory.FROM_AUDIO, ArtifactCategory.FROM_TRANSCRIPT, ArtifactCategory.FROM_LOG):
            invalidate_category(session_folder, category)


class GenerationStep(Enum):
    """One of the three outputs Session Detail's Generate (`G`) action can produce, in the
    dependency order `next_generation_step` walks: Role Transcript needs a machine Transcript;
    Ledger and Summary both need the Role Transcript.
    """

    ROLE_TRANSCRIPT = "role_transcript"
    LEDGER = "ledger"
    SUMMARY = "summary"


_GENERATION_ORDER: tuple[tuple[GenerationStep, ArtifactName], ...] = (
    (GenerationStep.ROLE_TRANSCRIPT, ArtifactName.ROLE_TRANSCRIPT),
    (GenerationStep.LEDGER, ArtifactName.LEDGER),
    (GenerationStep.SUMMARY, ArtifactName.SUMMARY),
)


def next_generation_step(session_folder: Path) -> GenerationStep | None:
    """The next missing step in `_GENERATION_ORDER`, or `None` if there's no machine Transcript
    yet (nothing can be generated) or every step already exists (nothing left to generate).

    The user cannot pick which output Generate produces -- each depends on the one before it, so
    there is always exactly one next step, not a choice.
    """
    existing = session_artifacts(session_folder)
    if not existing[ArtifactName.TRANSCRIPT]:
        return None
    for step, artifact_name in _GENERATION_ORDER:
        if not existing[artifact_name]:
            return step
    return None


def exportable_artifacts(session_folder: Path) -> list[ArtifactName]:
    """User-facing artifacts (`should_show_in_ui`) that currently exist -- same rule the indicator panel uses.

    Order matches `ARTIFACTS` (pipeline order), same as the indicator panel.
    """
    existing = session_artifacts(session_folder)
    return [name for name, spec in ARTIFACTS.items() if spec.should_show_in_ui and existing[name]]


def can_export_artifacts(session_folder: Path) -> tuple[bool, str | None]:
    if not exportable_artifacts(session_folder):
        return False, "No artifacts to export yet."
    return True, None


def export_artifact(session_folder: Path, artifact_name: ArtifactName, destination: Path) -> None:
    """Copy `artifact_name`'s file to `destination`. The source is untouched -- this is a plain copy, never a move."""
    with widelog.wide_event(
        op="export_artifact", session_folder=str(session_folder), artifact_name=artifact_name.value, destination=str(destination)
    ):
        shutil.copyfile(session_folder / ARTIFACTS[artifact_name].filename, destination)
