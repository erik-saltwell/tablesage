from __future__ import annotations

from pathlib import Path

from tablesage_application import Application
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.artifacts import (
    GenerationStep,
    delete_transcript_and_dependents,
    next_generation_step,
)
from tablesage_model.model import Campaign


def _touch(session_folder: Path, name: ArtifactName) -> None:
    (session_folder / ARTIFACTS[name].filename).write_text("{}")


def test_next_generation_step_is_none_without_a_transcript(tmp_path: Path) -> None:
    assert next_generation_step(tmp_path) is None


def test_next_generation_step_walks_role_transcript_then_ledger_then_summary(tmp_path: Path) -> None:
    _touch(tmp_path, ArtifactName.TRANSCRIPT)
    assert next_generation_step(tmp_path) is GenerationStep.ROLE_TRANSCRIPT

    _touch(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    assert next_generation_step(tmp_path) is GenerationStep.LEDGER

    _touch(tmp_path, ArtifactName.LEDGER)
    assert next_generation_step(tmp_path) is GenerationStep.SUMMARY

    _touch(tmp_path, ArtifactName.SUMMARY)
    assert next_generation_step(tmp_path) is None


def test_delete_transcript_and_dependents_removes_everything_but_input_audio(tmp_path: Path) -> None:
    for name in (
        ArtifactName.INPUT_AUDIO,
        ArtifactName.TRANSCRIPT,
        ArtifactName.TRANSCRIPT_TEXT,
        ArtifactName.REVIEWED_TRANSCRIPT,
        ArtifactName.ROLE_TRANSCRIPT,
        ArtifactName.TRANSCRIPT_BENCHMARK,
        ArtifactName.LEDGER,
        ArtifactName.SUMMARY,
    ):
        _touch(tmp_path, name)

    delete_transcript_and_dependents(tmp_path)

    assert (tmp_path / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).exists()
    for name in (
        ArtifactName.TRANSCRIPT,
        ArtifactName.TRANSCRIPT_TEXT,
        ArtifactName.REVIEWED_TRANSCRIPT,
        ArtifactName.ROLE_TRANSCRIPT,
        ArtifactName.TRANSCRIPT_BENCHMARK,
        ArtifactName.LEDGER,
        ArtifactName.SUMMARY,
    ):
        assert not (tmp_path / ARTIFACTS[name].filename).exists()


def test_application_next_generation_step_delegates_to_session_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    assert application.next_generation_step(game_session.id) is None

    _touch(application.session_folder(game_session.id), ArtifactName.TRANSCRIPT)

    assert application.next_generation_step(game_session.id) is GenerationStep.ROLE_TRANSCRIPT


def test_application_delete_transcript_deletes_derived_artifacts_only(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    _touch(session_folder, ArtifactName.INPUT_AUDIO)
    _touch(session_folder, ArtifactName.TRANSCRIPT)
    _touch(session_folder, ArtifactName.ROLE_TRANSCRIPT)
    _touch(session_folder, ArtifactName.LEDGER)

    application.delete_transcript(game_session.id)

    assert (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.LEDGER].filename).exists()
