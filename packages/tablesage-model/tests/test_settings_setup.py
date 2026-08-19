from __future__ import annotations

import re
from pathlib import Path

import pytest
from tablesage_model import setup

_DEFAULT_YAML = """
remove_outliers:
  min_sample_similarity: 0.6
  min_samples: 5
"""


def test_ensure_settings_deploys_default_on_first_run(tmp_path: Path) -> None:
    settings = setup.ensure_settings(tmp_path, _DEFAULT_YAML)

    settings_path = tmp_path / ".tablesage" / "settings.yaml"
    assert settings_path.exists()
    assert settings_path.read_text(encoding="utf-8") == _DEFAULT_YAML
    assert settings.remove_outliers.min_sample_similarity == 0.6
    assert settings.remove_outliers.min_samples == 5


def test_ensure_settings_loads_existing_file_without_overwriting(tmp_path: Path) -> None:
    settings_path = tmp_path / ".tablesage"
    settings_path.mkdir(parents=True)
    (settings_path / "settings.yaml").write_text(
        "remove_outliers:\n  min_sample_similarity: 0.9\n  min_samples: 3\n",
        encoding="utf-8",
    )

    settings = setup.ensure_settings(tmp_path, _DEFAULT_YAML)

    assert settings.remove_outliers.min_sample_similarity == 0.9
    assert settings.remove_outliers.min_samples == 3
    assert (settings_path / "settings.yaml").read_text(encoding="utf-8") != _DEFAULT_YAML


def test_ensure_settings_is_a_noop_on_second_call(tmp_path: Path) -> None:
    setup.ensure_settings(tmp_path, _DEFAULT_YAML)
    settings_path = tmp_path / ".tablesage" / "settings.yaml"
    settings_path.write_text("remove_outliers:\n  min_sample_similarity: 0.75\n  min_samples: 8\n", encoding="utf-8")

    settings = setup.ensure_settings(tmp_path, _DEFAULT_YAML)

    assert settings.remove_outliers.min_sample_similarity == 0.75
    assert settings.remove_outliers.min_samples == 8


def test_ensure_settings_raises_with_file_path_on_invalid_yaml(tmp_path: Path) -> None:
    settings_dir = tmp_path / ".tablesage"
    settings_dir.mkdir(parents=True)
    (settings_dir / "settings.yaml").write_text("remove_outliers:\n  min_sample_similarity: [", encoding="utf-8")

    with pytest.raises(ValueError, match=re.escape(str(settings_dir / "settings.yaml"))):
        setup.ensure_settings(tmp_path, _DEFAULT_YAML)


def test_ensure_settings_raises_with_file_path_on_out_of_range_value(tmp_path: Path) -> None:
    settings_dir = tmp_path / ".tablesage"
    settings_dir.mkdir(parents=True)
    (settings_dir / "settings.yaml").write_text("remove_outliers:\n  min_sample_similarity: 1.5\n  min_samples: 5\n", encoding="utf-8")

    with pytest.raises(ValueError, match=re.escape(str(settings_dir / "settings.yaml"))):
        setup.ensure_settings(tmp_path, _DEFAULT_YAML)
