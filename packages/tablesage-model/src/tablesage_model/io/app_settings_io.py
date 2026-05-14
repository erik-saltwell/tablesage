from __future__ import annotations

from .. import _paths
from .._settings import AppSettings
from .yaml_io import load_model_from_yaml, save_model_to_yaml


def load_app_settings() -> AppSettings:
    path = _paths.app_settings_path()
    if not path.exists():
        return AppSettings()
    return load_model_from_yaml(path, AppSettings)


def save_app_settings(settings: AppSettings) -> None:
    save_model_to_yaml(_paths.app_settings_path(), settings)
