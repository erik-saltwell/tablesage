from __future__ import annotations

from pathlib import Path

import pytest
from tablesage_model import _paths
from tablesage_model._actions.invalidation import InputChange, invalidate
from tablesage_model._settings import AppSettings


def _seed_all_artifacts(campaign_slug: str, session_slug: str, app_settings: AppSettings) -> dict[str, Path]:
    session_dir = _paths.session_dir(campaign_slug, session_slug)
    _paths.ensure_dir(session_dir)

    raw_audio = session_dir / "session-one-raw.m4a"
    cleaned_audio = session_dir / app_settings.cleaned_audio_file
    transcript = session_dir / _paths.KnownFiles.TRANSCRIPT
    summary = session_dir / _paths.KnownFiles.SUMMARY

    raw_audio.write_bytes(b"raw")
    cleaned_audio.write_bytes(b"cleaned")
    transcript.write_text("transcript body", encoding="utf-8")
    summary.write_text("summary body", encoding="utf-8")

    return {
        "raw_audio": raw_audio,
        "cleaned_audio": cleaned_audio,
        "transcript": transcript,
        "summary": summary,
    }


def test_summary_rerun_deletes_only_summary() -> None:
    app_settings = AppSettings()
    paths = _seed_all_artifacts("sable-crown", "session-one", app_settings)

    invalidate("sable-crown", "session-one", InputChange.SUMMARY_RERUN, app_settings)

    assert not paths["summary"].exists()
    assert paths["transcript"].exists()
    assert paths["cleaned_audio"].exists()
    assert paths["raw_audio"].exists()


@pytest.mark.parametrize("change", list(InputChange))
def test_invalidate_is_idempotent_when_no_artifacts_present(change: InputChange) -> None:
    app_settings = AppSettings()
    _paths.ensure_dir(_paths.session_dir("sable-crown", "session-one"))

    invalidate("sable-crown", "session-one", change, app_settings)
    invalidate("sable-crown", "session-one", change, app_settings)


@pytest.mark.parametrize(
    "change",
    [InputChange.PROCESS_SESSION_RERUN, InputChange.AUDIO_REPLACED, InputChange.ATTENDEES_EDITED],
)
def test_destructive_changes_delete_all_downstream_artifacts(change: InputChange) -> None:
    app_settings = AppSettings()
    paths = _seed_all_artifacts("sable-crown", "session-one", app_settings)

    invalidate("sable-crown", "session-one", change, app_settings)

    assert not paths["summary"].exists()
    assert not paths["transcript"].exists()
    assert not paths["cleaned_audio"].exists()
    assert paths["raw_audio"].exists()
