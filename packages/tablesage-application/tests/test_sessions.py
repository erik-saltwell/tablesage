from __future__ import annotations

import wave
from datetime import date
from pathlib import Path

import pytest
from tablesage_application import Application
from tablesage_application.sessions import PROCESSED_SESSION_FILENAME, SESSION_SUMMARY_FILENAME
from tablesage_model.model import GAME_MASTER_ROLE, Campaign, Player
from tablesage_tools.embeddings import Embedding


def _write_wav(path: Path, *, num_frames: int = 16000, framerate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(framerate)
        wav_file.writeframes(b"\x00\x00" * num_frames)


def test_create_session_assigns_sequence_number_and_creates_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))

    first = application.create_session(campaign.id, "Session One", date(2026, 1, 1))
    second = application.create_session(campaign.id, "Session Two", date(2026, 1, 8))

    assert first.sequence_number == 1
    assert second.sequence_number == 2
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001").is_dir()
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "002").is_dir()


def test_sequence_numbers_are_never_reused_after_deletion(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.create_session(campaign.id, "Session One")

    # directly exercise that the next sequence is max()+1, not count()+1
    third = application.create_session(campaign.id, "Session Two")
    assert third.sequence_number == 2


def test_list_sessions_scoped_to_campaign(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign_a = application.create_campaign(Campaign(name="Campaign A"))
    campaign_b = application.create_campaign(Campaign(name="Campaign B"))
    application.create_session(campaign_a.id, "A1")
    application.create_session(campaign_b.id, "B1")

    sessions_a = application.list_sessions(campaign_a.id)
    assert [s.name for s in sessions_a] == ["A1"]


def test_last_session_dates_computed_dynamically(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.create_session(campaign.id, "Session One", date(2026, 1, 1))
    application.create_session(campaign.id, "Session Two", date(2026, 1, 8))

    last_dates = application.last_session_dates()

    assert last_dates[campaign.id] == date(2026, 1, 8)


def test_cleanup_orphan_session_dirs_removes_only_unknown_folders(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.create_session(campaign.id, "Session One")

    orphan = tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "999"
    orphan.mkdir()

    removed = application.cleanup_orphan_session_dirs(campaign.id)

    assert removed == ["999"]
    assert not orphan.exists()
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001").is_dir()


def test_get_session_raises_for_unknown_id(tmp_path: Path) -> None:
    application = Application(tmp_path)

    with pytest.raises(ValueError, match="not found"):
        application.get_session(Campaign(name="whatever").id)


def test_update_session_changes_name_and_date_no_fs_side_effect(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    updated = application.update_session(game_session.id, "Session One (renamed)", date(2026, 3, 1))

    assert updated.name == "Session One (renamed)"
    assert updated.session_date == date(2026, 3, 1)
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001").is_dir()


def test_delete_session_removes_row_but_keeps_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    application.delete_session(game_session.id)

    assert application.list_sessions(campaign.id) == []
    assert (tmp_path / ".tablesage" / "campaigns" / "Iron Pact" / "001").is_dir()


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


def test_add_attendance_seeds_role_translating_game_master(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    gm = application.create_player(Player(name="Gary"))
    application.add_player_to_campaign(campaign.id, gm.id, GAME_MASTER_ROLE)
    character = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, character.id, "Zaria the Bold")

    gm_attendee = application.add_attendance(game_session.id, gm.id)
    character_attendee = application.add_attendance(game_session.id, character.id)

    assert gm_attendee.roles == ("Game Master",)
    assert character_attendee.roles == ("Zaria the Bold",)


def test_add_attendance_rejects_non_roster_player(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))

    with pytest.raises(ValueError, match="not a member of the campaign roster"):
        application.add_attendance(game_session.id, player.id)


def test_add_attendance_rejects_duplicate(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Alice's Character")
    application.add_attendance(game_session.id, player.id)

    with pytest.raises(ValueError, match="already attending"):
        application.add_attendance(game_session.id, player.id)


def test_remove_attendance_removes_row(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Alice's Character")
    attendee = application.add_attendance(game_session.id, player.id)

    application.remove_attendance(game_session.id, attendee.attendance_id)

    assert application.list_attendance(game_session.id) == []


def test_set_attendance_roles_replaces_full_set(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    attendee = application.add_attendance(game_session.id, player.id)

    updated = application.set_attendance_roles(game_session.id, attendee.attendance_id, ["Zaria the Bold", "Narrator"])

    assert updated.roles == ("Zaria the Bold", "Narrator")


def test_set_attendance_roles_rejects_empty_list(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    attendee = application.add_attendance(game_session.id, player.id)

    with pytest.raises(ValueError, match="At least one role"):
        application.set_attendance_roles(game_session.id, attendee.attendance_id, ["   "])


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
