from __future__ import annotations

import shutil
from pathlib import Path

import widelog

from ..paths import ARTIFACTS, LEDGER_PAIR_MARKER, ArtifactName


def delete_artifact(session_folder: Path, artifact_name: ArtifactName) -> None:
    """Delete an artifact's canonical file and every deterministic companion view."""
    spec = ARTIFACTS[artifact_name]
    (session_folder / spec.filename).unlink(missing_ok=True)
    for companion_filename in spec.companion_filenames:
        (session_folder / companion_filename).unlink(missing_ok=True)
    if artifact_name is ArtifactName.LEDGER:
        (session_folder / ARTIFACTS[ArtifactName.SCENE_BREAKDOWN].filename).unlink(missing_ok=True)
        (session_folder / LEDGER_PAIR_MARKER).unlink(missing_ok=True)


def session_artifacts(session_folder: Path) -> dict[ArtifactName, bool]:
    """What exists on disk for a session -- drives the indicator panel and the P/G/T gates."""
    existing = {name: (session_folder / spec.filename).is_file() for name, spec in ARTIFACTS.items()}
    if (session_folder / LEDGER_PAIR_MARKER).exists():
        for name in (ArtifactName.LEDGER, ArtifactName.SCENE_BREAKDOWN, ArtifactName.RECAP_SUMMARY, ArtifactName.SUMMARY):
            existing[name] = False
    return existing


def delete_all_artifacts(session_folder: Path) -> None:
    """Delete every artifact for this session, including the raw input audio.

    Backs Session Detail's Clean Session (`C`) action -- the one place in the app that deletes
    `IMPORTED`-category files, unlike every other invalidation path.
    """
    with widelog.wide_event(op="delete_all_artifacts", session_folder=str(session_folder)):
        for name in ARTIFACTS:
            delete_artifact(session_folder, name)


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
