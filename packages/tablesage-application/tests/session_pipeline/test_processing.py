from __future__ import annotations

import wave
from pathlib import Path

import pytest
from tablesage_application import Application
from tablesage_application.session_pipeline.processing import PROCESSED_SESSION_FILENAME, SESSION_SUMMARY_FILENAME
from tablesage_model.model import GAME_MASTER_ROLE, Campaign, Player
from tablesage_tools.embeddings import Embedding


def _write_wav(path: Path, *, num_frames: int = 16000, framerate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(framerate)
        wav_file.writeframes(b"\x00\x00" * num_frames)


def test_session_artifacts_reflect_filesystem_state(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    artifacts = application.session_artifacts(game_session.id)
    assert not artifacts.has_input_audio
    assert not artifacts.has_processed_session
    assert not artifacts.has_summary

    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")

    artifacts = application.session_artifacts(game_session.id)
    assert artifacts.has_processed_session
    assert not artifacts.has_input_audio
    assert not artifacts.has_summary


def _stub_clean(source: Path, target: Path) -> None:
    """Stand in for `Application._clean_session_audio` -- a plain copy, no ffmpeg/ML involved."""
    target.write_bytes(source.read_bytes())


def test_import_session_audio_copies_file_under_fixed_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    monkeypatch.setattr(application, "_clean_session_audio", _stub_clean)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    source = tmp_path / "recording.mp3"
    source.write_bytes(b"fake audio bytes")

    application.import_session_audio(game_session.id, source)

    assert application.session_artifacts(game_session.id).has_input_audio


def test_import_session_audio_raises_for_missing_file(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    with pytest.raises(ValueError, match="not a file"):
        application.import_session_audio(game_session.id, tmp_path / "missing.wav")


def test_import_session_audio_invalidates_stale_downstream_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    monkeypatch.setattr(application, "_clean_session_audio", _stub_clean)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")
    (folder / SESSION_SUMMARY_FILENAME).write_text("summary")

    source = tmp_path / "recording.wav"
    source.write_bytes(b"fake audio bytes")
    application.import_session_audio(game_session.id, source)

    artifacts = application.session_artifacts(game_session.id)
    assert artifacts.has_input_audio
    assert not artifacts.has_processed_session
    assert not artifacts.has_summary


def test_import_session_audio_keeps_downstream_artifacts_when_clean_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _failing_clean(source: Path, target: Path) -> None:
        raise RuntimeError("ffmpeg exploded")

    application = Application(tmp_path)
    monkeypatch.setattr(application, "_clean_session_audio", _failing_clean)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001"
    (folder / PROCESSED_SESSION_FILENAME).write_text("{}")
    (folder / SESSION_SUMMARY_FILENAME).write_text("summary")

    source = tmp_path / "recording.wav"
    source.write_bytes(b"fake audio bytes")
    with pytest.raises(RuntimeError, match="ffmpeg exploded"):
        application.import_session_audio(game_session.id, source)

    artifacts = application.session_artifacts(game_session.id)
    assert not artifacts.has_input_audio
    assert artifacts.has_processed_session
    assert artifacts.has_summary
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


def test_can_process_session_requires_input_audio_two_attendees_and_centroids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    monkeypatch.setattr(application, "_clean_session_audio", _stub_clean)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    enabled, reason = application.can_process_session(game_session.id)
    assert not enabled
    assert reason == "Import input audio first."

    source = tmp_path / "recording.wav"
    source.write_bytes(b"fake audio bytes")
    application.import_session_audio(game_session.id, source)

    alice = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, alice.id, GAME_MASTER_ROLE)
    application.add_attendance(game_session.id, alice.id)

    enabled, reason = application.can_process_session(game_session.id)
    assert not enabled
    assert reason == "At least 2 attendees are required."

    bob = application.create_player(Player(name="Bob"))
    application.add_player_to_campaign(campaign.id, bob.id, "Bob's Character")
    application.add_attendance(game_session.id, bob.id)

    enabled, reason = application.can_process_session(game_session.id)
    assert not enabled
    assert reason is not None and "Missing voice profile" in reason
    assert "Alice" in reason
    assert "Bob" in reason

    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))
    _write_wav(tmp_path / ".tablesage" / "players" / "Alice" / "clip.wav")
    _write_wav(tmp_path / ".tablesage" / "players" / "Bob" / "clip.wav")
    application.recompute_centroid(alice.id)
    application.recompute_centroid(bob.id)

    enabled, reason = application.can_process_session(game_session.id)
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
    assert not artifacts.has_processed_session
    assert not artifacts.has_summary
