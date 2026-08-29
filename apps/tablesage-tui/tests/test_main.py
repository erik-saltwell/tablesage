from __future__ import annotations

from pathlib import Path

import pytest
from tablesage_model.settings import AppSettings
from tablesage_model.setup import ensure_settings
from tablesage_tui.resources import load_resource
from tablesage_tui.screens import main_app


def test_packaged_settings_yaml_deploys_and_loads_with_expected_defaults(tmp_path: Path) -> None:
    default_yaml = load_resource("settings.yaml")

    settings = ensure_settings(tmp_path, default_yaml)

    assert (tmp_path / ".tablesage" / "settings.yaml").exists()
    assert settings.remove_outliers.min_sample_similarity == 0.6
    assert settings.remove_outliers.min_samples == 5
    assert settings.speaker_identification.similarity_margin_threshold == 0.1
    assert settings.speaker_identification.duration_override.min_seconds == 1.0
    assert settings.speaker_identification.duration_override.similarity_margin_threshold == 0.04
    assert settings.speaker_identification.short_utterance_widening.enabled is True
    assert settings.speaker_identification.short_utterance_widening.max_original_duration_seconds == 0.75
    assert settings.speaker_identification.short_utterance_widening.target_duration_seconds == 1.0
    assert settings.speaker_identification.short_utterance_widening.max_neighbor_gap_seconds == 2.0
    assert settings.speaker_identification.cluster_propagation.enabled is True
    assert settings.speaker_identification.cluster_propagation.evidence_min_duration_seconds == 0.5
    assert settings.speaker_identification.cluster_propagation.max_utterance_duration_seconds == 0.5
    assert settings.speaker_identification.cluster_propagation.cluster_margin_threshold == 0.0
    assert settings.speaker_identification.cluster_propagation.contradiction_veto_margin_threshold == 0.02
    assert settings.speaker_identification.existing_player_match_similarity_margin_threshold == 0.08
    assert settings.speaker_identification.allow_unassigned is True


def test_packaged_settings_yaml_is_not_redeployed_over_user_edits(tmp_path: Path) -> None:
    default_yaml = load_resource("settings.yaml")
    ensure_settings(tmp_path, default_yaml)

    settings_path = tmp_path / ".tablesage" / "settings.yaml"
    settings_path.write_text("remove_outliers:\n  min_sample_similarity: 0.42\n  min_samples: 9\n", encoding="utf-8")

    settings = ensure_settings(tmp_path, default_yaml)

    assert settings.remove_outliers.min_sample_similarity == 0.42
    assert settings.remove_outliers.min_samples == 9


def test_main_deploys_settings_and_injects_them_into_application(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercises `main()` itself -- the real composition root -- not a reimplementation of it."""
    monkeypatch.chdir(tmp_path)
    settings_dir = tmp_path / ".tablesage"
    settings_dir.mkdir()
    (settings_dir / "settings.yaml").write_text("remove_outliers:\n  min_sample_similarity: 0.33\n  min_samples: 2\n", encoding="utf-8")

    captured: dict[str, AppSettings | None] = {}

    class FakeApplication:
        def __init__(self, settings: AppSettings | None = None) -> None:
            captured["settings"] = settings

    monkeypatch.setattr(main_app, "Application", FakeApplication)
    monkeypatch.setattr(main_app.TableSageApp, "run", lambda self: None)

    main_app.main()

    settings = captured["settings"]
    assert settings is not None
    assert settings.remove_outliers.min_sample_similarity == 0.33
    assert settings.remove_outliers.min_samples == 2
