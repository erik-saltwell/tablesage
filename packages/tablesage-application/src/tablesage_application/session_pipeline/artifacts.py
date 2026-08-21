from __future__ import annotations

from pathlib import Path

from ..paths import ARTIFACTS, ArtifactName


def session_artifacts(session_folder: Path) -> dict[ArtifactName, bool]:
    """What exists on disk for a session -- drives the indicator panel and the P/G/T gates."""
    return {name: (session_folder / spec.filename).is_file() for name, spec in ARTIFACTS.items()}
