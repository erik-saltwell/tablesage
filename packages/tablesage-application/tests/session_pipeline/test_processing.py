from __future__ import annotations

import uuid
import wave
from pathlib import Path

import pytest
from sqlmodel import Session
from tablesage_application import Application, session_pipeline
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_model.model import GAME_MASTER_ROLE, Campaign, Player
from tablesage_tools.embeddings import Embedding

PROCESSED_SESSION_FILENAME = ARTIFACTS[ArtifactName.PROCESSED_SESSION].filename
SESSION_SUMMARY_FILENAME = ARTIFACTS[ArtifactName.SUMMARY].filename


def _write_wav(path: Path, *, num_frames: int = 16000, framerate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(framerate)
        wav_file.writeframes(b"\x00\x00" * num_frames)


def _stub_clean_clip(source: Path, target: Path, *, normalize: bool = False) -> None:
    """Stand in for `tablesage_tools.audio.clean_clip` -- a plain copy, no ffmpeg/ML involved."""
    target.write_bytes(source.read_bytes())


async def _async_stub_clean_clip(source: Path, target: Path, *, normalize: bool = False) -> None:
    _stub_clean_clip(source, target, normalize=normalize)


def _import_audio(application: Application, session_id: uuid.UUID, source: Path, *, normalize_volume: bool = False) -> None:
    session_pipeline.import_audio.import_audio(source, application.session_folder(session_id), normalize_volume)


def test_session_artifacts_reflect_filesystem_state(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    artifacts = application.session_artifacts(game_session.id)
    assert not artifacts[ArtifactName.INPUT_AUDIO]
    assert not artifacts[ArtifactName.PROCESSED_SESSION]
    assert not artifacts[ArtifactName.SUMMARY]

    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")

    artifacts = application.session_artifacts(game_session.id)
    assert artifacts[ArtifactName.PROCESSED_SESSION]
    assert not artifacts[ArtifactName.INPUT_AUDIO]
    assert not artifacts[ArtifactName.SUMMARY]


def test_import_session_audio_copies_file_under_fixed_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_pipeline.import_audio, "clean_clip", _async_stub_clean_clip)
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    source = tmp_path / "recording.mp3"
    source.write_bytes(b"fake audio bytes")

    _import_audio(application, game_session.id, source)

    assert application.session_artifacts(game_session.id)[ArtifactName.INPUT_AUDIO]


def test_import_session_audio_raises_for_missing_file(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    with pytest.raises(ValueError, match="not a file"):
        _import_audio(application, game_session.id, tmp_path / "missing.wav")


def test_import_session_audio_invalidates_stale_downstream_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_pipeline.import_audio, "clean_clip", _async_stub_clean_clip)
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")
    (folder / SESSION_SUMMARY_FILENAME).write_text("summary")

    source = tmp_path / "recording.wav"
    source.write_bytes(b"fake audio bytes")
    _import_audio(application, game_session.id, source)

    artifacts = application.session_artifacts(game_session.id)
    assert artifacts[ArtifactName.INPUT_AUDIO]
    assert not artifacts[ArtifactName.PROCESSED_SESSION]
    assert not artifacts[ArtifactName.SUMMARY]


def test_import_session_audio_keeps_downstream_artifacts_when_clean_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _failing_clean(source: Path, target: Path, *, normalize: bool = False) -> None:
        raise RuntimeError("ffmpeg exploded")

    monkeypatch.setattr(session_pipeline.import_audio, "clean_clip", _failing_clean)
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")
    (folder / SESSION_SUMMARY_FILENAME).write_text("summary")

    source = tmp_path / "recording.wav"
    source.write_bytes(b"fake audio bytes")
    with pytest.raises(RuntimeError, match="ffmpeg exploded"):
        _import_audio(application, game_session.id, source)

    artifacts = application.session_artifacts(game_session.id)
    assert not artifacts[ArtifactName.INPUT_AUDIO]
    assert artifacts[ArtifactName.PROCESSED_SESSION]
    assert artifacts[ArtifactName.SUMMARY]
    assert list(folder.glob("*.tmp")) == []


def test_validate_import_audio_source_rejects_unrecognized_extension(tmp_path: Path) -> None:
    application = Application(tmp_path)
    source = tmp_path / "notes.txt"
    source.write_text("not audio")

    with pytest.raises(ValueError, match="isn't a recognized audio file"):
        application.validate_import_audio_source(source)


def test_validate_import_audio_source_accepts_common_audio_extensions(tmp_path: Path) -> None:
    application = Application(tmp_path)
    source = tmp_path / "recording.m4a"
    source.write_bytes(b"fake audio bytes")

    application.validate_import_audio_source(source)  # no raise


def _can_process_session(application: Application, session_id: uuid.UUID) -> tuple[bool, str | None]:
    """`Application` no longer wraps this (nothing on the TUI side calls it since the `P`
    binding was removed) -- `processing.can_process_session` itself is still live/tested."""
    session_folder = application.session_folder(session_id)
    with Session(application._engine) as session:
        return session_pipeline.processing.can_process_session(session, session_id, session_folder)


def test_can_process_session_requires_input_audio_two_attendees_and_centroids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_pipeline.import_audio, "clean_clip", _async_stub_clean_clip)
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    enabled, reason = _can_process_session(application, game_session.id)
    assert not enabled
    assert reason == "Import input audio first."

    source = tmp_path / "recording.wav"
    source.write_bytes(b"fake audio bytes")
    _import_audio(application, game_session.id, source)

    alice = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, alice.id, GAME_MASTER_ROLE)
    application.add_attendance(game_session.id, alice.id)

    enabled, reason = _can_process_session(application, game_session.id)
    assert not enabled
    assert reason == "At least 2 attendees are required."

    bob = application.create_player(Player(name="Bob"))
    application.add_player_to_campaign(campaign.id, bob.id, "Bob's Character")
    application.add_attendance(game_session.id, bob.id)

    enabled, reason = _can_process_session(application, game_session.id)
    assert not enabled
    assert reason is not None and "Missing voice profile" in reason
    assert "Alice" in reason
    assert "Bob" in reason

    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))
    _write_wav(tmp_path / ".tablesage" / "players" / "Alice" / "clip.wav")
    _write_wav(tmp_path / ".tablesage" / "players" / "Bob" / "clip.wav")
    application.recompute_centroid(alice.id)
    application.recompute_centroid(bob.id)

    enabled, reason = _can_process_session(application, game_session.id)
    assert enabled
    assert reason is None


def test_can_generate_summary_requires_processed_session(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    enabled, reason = application.can_generate_summary(game_session.id)
    assert not enabled
    assert reason == "Process the session first."

    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")

    enabled, reason = application.can_generate_summary(game_session.id)
    assert enabled
    assert reason is None


def test_can_transcribe_audio_requires_input_audio_and_attendees(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_pipeline.import_audio, "clean_clip", _async_stub_clean_clip)
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    enabled, reason = application.can_transcribe_audio(game_session.id)
    assert not enabled
    assert reason == "Import input audio first."

    source = tmp_path / "recording.wav"
    source.write_bytes(b"fake audio bytes")
    _import_audio(application, game_session.id, source)

    enabled, reason = application.can_transcribe_audio(game_session.id)
    assert not enabled
    assert reason == "Add attendees before transcribing."

    alice = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, alice.id, GAME_MASTER_ROLE)
    application.add_attendance(game_session.id, alice.id)

    enabled, reason = application.can_transcribe_audio(game_session.id)
    assert not enabled
    assert reason is not None and "Missing voice profile" in reason
    assert "Alice" in reason

    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))
    _write_wav(tmp_path / ".tablesage" / "players" / "Alice" / "clip.wav")
    application.recompute_centroid(alice.id)

    enabled, reason = application.can_transcribe_audio(game_session.id)
    assert enabled
    assert reason is None


def test_can_export_artifacts_requires_a_user_facing_artifact(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    enabled, reason = application.can_export_artifacts(game_session.id)
    assert not enabled
    assert reason == "No artifacts to export yet."

    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    # PROCESSED_SESSION exists but isn't should_show_in_ui -- must not count.
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")
    enabled, reason = application.can_export_artifacts(game_session.id)
    assert not enabled
    assert reason == "No artifacts to export yet."

    (folder / SESSION_SUMMARY_FILENAME).write_text("summary")
    enabled, reason = application.can_export_artifacts(game_session.id)
    assert enabled
    assert reason is None


def test_exportable_artifacts_excludes_non_ui_artifacts(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")
    (folder / SESSION_SUMMARY_FILENAME).write_text("summary")

    assert application.exportable_artifacts(game_session.id) == [ArtifactName.SUMMARY]


def test_export_artifact_copies_file_without_deleting_source(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / SESSION_SUMMARY_FILENAME).write_text("summary contents")
    destination = tmp_path / "exported-summary.md"

    application.export_artifact(game_session.id, ArtifactName.SUMMARY, destination)

    assert destination.read_text() == "summary contents"
    assert (folder / SESSION_SUMMARY_FILENAME).read_text() == "summary contents"


def test_export_artifact_overwrites_existing_destination(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / SESSION_SUMMARY_FILENAME).write_text("new contents")
    destination = tmp_path / "exported-summary.md"
    destination.write_text("stale contents")

    application.export_artifact(game_session.id, ArtifactName.SUMMARY, destination)

    assert destination.read_text() == "new contents"


def test_attendance_mutation_invalidates_stale_downstream_artifacts(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")

    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")
    (folder / SESSION_SUMMARY_FILENAME).write_text("summary")

    application.add_attendance(game_session.id, player.id)

    artifacts = application.session_artifacts(game_session.id)
    assert not artifacts[ArtifactName.PROCESSED_SESSION]
    assert not artifacts[ArtifactName.SUMMARY]
