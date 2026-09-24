from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from tablesage_model.settings import AppSettings
from tablesage_model.setup import ensure_settings
from tablesage_tui.resources import load_resource
from tablesage_tui.screens import main_app
from textual.app import App


def test_error_notifications_do_not_expire() -> None:
    app = main_app.TableSageApp()

    with patch.object(App, "notify") as notify:
        app.notify("Something failed", severity="error")

    notify.assert_called_once_with(
        "Something failed",
        title="",
        severity="error",
        timeout=float("inf"),
        markup=True,
    )


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
    assert settings.speaker_identification.allow_unassigned is True
    assert settings.llm_model_high == "openai/gpt-6-astra"


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
    monkeypatch.setattr(main_app, "ensure_media_tools", lambda: None)
    monkeypatch.setattr(main_app.TableSageApp, "run", lambda self: None)

    main_app.main()

    settings = captured["settings"]
    assert settings is not None
    assert settings.remove_outliers.min_sample_similarity == 0.33
    assert settings.remove_outliers.min_samples == 2


def test_main_ignores_launch_directory_env_without_overriding_exports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TABLESAGE_TEST_LOCAL", raising=False)
    monkeypatch.setenv("TABLESAGE_TEST_EXPORTED", "shell-value")
    (tmp_path / ".env").write_text("TABLESAGE_TEST_LOCAL=workspace-value\nTABLESAGE_TEST_EXPORTED=file-value\n", encoding="utf-8")
    monkeypatch.setattr(main_app, "ensure_media_tools", lambda: None)
    monkeypatch.setattr(main_app.TableSageApp, "run", lambda self: None)

    main_app.main()

    import os

    assert "TABLESAGE_TEST_LOCAL" not in os.environ
    assert os.environ["TABLESAGE_TEST_EXPORTED"] == "shell-value"


def test_main_stops_before_creating_workspace_when_media_tools_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tablesage_tui import startup

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(startup, "which", lambda name: None if name == "ffplay" else "/usr/bin/ffmpeg")
    with pytest.raises(SystemExit, match="requires ffplay on PATH") as exc:
        main_app.main()
    assert "https://ffmpeg.org/download.html" in str(exc.value)
    assert not (tmp_path / ".tablesage").exists()
