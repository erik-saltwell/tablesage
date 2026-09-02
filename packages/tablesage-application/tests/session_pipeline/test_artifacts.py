from __future__ import annotations

from pathlib import Path

from tablesage_application import Application
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.artifacts import delete_all_artifacts
from tablesage_model.model import Campaign


def _touch(session_folder: Path, name: ArtifactName) -> None:
    (session_folder / ARTIFACTS[name].filename).write_text("{}")


def test_delete_all_artifacts_removes_everything_including_input_audio(tmp_path: Path) -> None:
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
    (tmp_path / "ledger.md").write_text("readable")

    delete_all_artifacts(tmp_path)

    for name in ARTIFACTS:
        assert not (tmp_path / ARTIFACTS[name].filename).exists()
    assert not (tmp_path / "ledger.md").exists()


def test_application_clean_session_deletes_everything_including_input_audio(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    _touch(session_folder, ArtifactName.INPUT_AUDIO)
    _touch(session_folder, ArtifactName.TRANSCRIPT)
    _touch(session_folder, ArtifactName.ROLE_TRANSCRIPT)
    _touch(session_folder, ArtifactName.LEDGER)
    (session_folder / "ledger.md").write_text("readable")

    application.clean_session(game_session.id)

    assert not (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename).exists()
    assert not (session_folder / ARTIFACTS[ArtifactName.LEDGER].filename).exists()
    assert not (session_folder / "ledger.md").exists()
