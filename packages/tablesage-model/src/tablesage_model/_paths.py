from __future__ import annotations

from pathlib import Path


def _resolve_tablesage_dir(cwd: Path | None = None) -> Path:
    cwd_actual: Path = cwd if cwd is not None else Path.cwd()
    tablesage_dir = cwd_actual / ".tablesage"
    tablesage_dir.mkdir(parents=True, exist_ok=True)
    return tablesage_dir


def resolve_database_path(cwd: Path | None = None) -> Path:
    return _resolve_tablesage_dir(cwd) / "tablesage.db"


def resolve_settings_path(cwd: Path | None = None) -> Path:
    return _resolve_tablesage_dir(cwd) / "settings.yaml"
