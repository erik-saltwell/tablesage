from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from .._paths import resolve_settings_path
from ..settings import AppSettings


def ensure_settings(cwd: Path | None, default_yaml: str) -> AppSettings:
    """Deploy the packaged default settings file into `.tablesage/settings.yaml` on first
    run, then load and validate whatever is there.

    A settings file that already exists is loaded as-is and never overwritten,
    so user edits persist across runs -- `default_yaml` only seeds a fresh
    `.tablesage` directory (e.g. the first run after a `uv tool`/`uvx` deploy).
    """
    settings_path = resolve_settings_path(cwd)
    if not settings_path.exists():
        settings_path.write_text(default_yaml, encoding="utf-8")

    try:
        data = yaml.safe_load(settings_path.read_text(encoding="utf-8")) or {}
        return AppSettings.model_validate(data)
    except (yaml.YAMLError, ValidationError) as exc:
        msg = f"Invalid settings file at {settings_path}: {exc}"
        raise ValueError(msg) from exc
