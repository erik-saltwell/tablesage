from __future__ import annotations

from pathlib import Path


def resolve_database_path(cwd: Path | None = None) -> Path:
    cwd_actual: Path = Path.cwd()

    if cwd is not None:
        cwd_actual = cwd

    return_path: Path = cwd_actual / ".tablesage"
    return_path.mkdir(parents=True, exist_ok=True)
    return_path = return_path / "tablesage.db"
    return return_path
