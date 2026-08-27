from __future__ import annotations

import shutil
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
