from __future__ import annotations

import wave
from pathlib import Path

import pytest
from tablesage_application import Application
from tablesage_application.players import VoiceClip
from tablesage_model.model import Player
from tablesage_tools.embeddings import Embedding


def _write_wav(path: Path, *, num_frames: int = 16000, framerate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(framerate)
        wav_file.writeframes(b"\x00\x00" * num_frames)


def test_create_player_creates_db_row_and_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)

    created = application.create_player(Player(name="Alice"))

    assert created.id is not None
    assert created.sample_count == 0
    assert (tmp_path / ".tablesage" / "players" / "Alice").is_dir()


def test_create_player_rejects_duplicate_name(tmp_path: Path) -> None:
    application = Application(tmp_path)
    application.create_player(Player(name="Alice"))

    with pytest.raises(ValueError, match="already exists"):
        application.create_player(Player(name="Alice"))


def test_rename_player_renames_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))

    renamed = application.rename_player(player.id, "Alicia")

    assert renamed.name == "Alicia"
    assert not (tmp_path / ".tablesage" / "players" / "Alice").exists()
    assert (tmp_path / ".tablesage" / "players" / "Alicia").is_dir()


def test_rename_player_rejects_duplicate_name(tmp_path: Path) -> None:
    application = Application(tmp_path)
    application.create_player(Player(name="Alice"))
    bob = application.create_player(Player(name="Bob"))

    with pytest.raises(ValueError, match="already exists"):
        application.rename_player(bob.id, "Alice")

    # rollback should leave Bob's folder untouched under his original name
    assert (tmp_path / ".tablesage" / "players" / "Bob").is_dir()


def test_delete_player_removes_row_but_keeps_folder(tmp_path: Path) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))

    application.delete_player(player.id)

    assert application.list_players() == []
    assert (tmp_path / ".tablesage" / "players" / "Alice").is_dir()


def test_cleanup_orphan_player_dirs_removes_only_unknown_folders(tmp_path: Path) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    application.delete_player(player.id)
    application.create_player(Player(name="Bob"))

    removed = application.cleanup_orphan_player_dirs()

    assert removed == ["Alice"]
    assert not (tmp_path / ".tablesage" / "players" / "Alice").exists()
    assert (tmp_path / ".tablesage" / "players" / "Bob").is_dir()


def test_list_voice_clips_returns_empty_when_no_clips(tmp_path: Path) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))

    assert application.list_voice_clips(player.id) == []


def test_list_voice_clips_lists_wav_files_with_duration(tmp_path: Path) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    _write_wav(folder / "clip_001.wav", num_frames=16000, framerate=16000)
    _write_wav(folder / "clip_002.wav", num_frames=8000, framerate=16000)
    (folder / "notes.txt").write_text("not a clip")

    clips = application.list_voice_clips(player.id)

    assert clips == [
        VoiceClip(filename="clip_001.wav", duration_seconds=1.0),
        VoiceClip(filename="clip_002.wav", duration_seconds=0.5),
    ]


def test_recompute_centroid_uses_injected_embedder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    _write_wav(folder / "clip_001.wav")
    _write_wav(folder / "clip_002.wav")

    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    updated = application.recompute_centroid(player.id)

    assert updated.sample_count == 2
    assert updated.embedding_dimension == 2
    assert updated.centroid_embedding is not None
    assert updated.computed_at is not None


def test_recompute_centroid_clears_when_no_clips(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    _write_wav(folder / "clip_001.wav")
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))
    application.recompute_centroid(player.id)

    (folder / "clip_001.wav").unlink()
    updated = application.recompute_centroid(player.id)

    assert updated.sample_count == 0
    assert updated.centroid_embedding is None
    assert updated.embedding_dimension is None
    assert updated.computed_at is None


def test_delete_voice_clip_removes_file_and_recomputes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    _write_wav(folder / "clip_001.wav")
    _write_wav(folder / "clip_002.wav")
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    updated = application.delete_voice_clip(player.id, "clip_001.wav")

    assert not (folder / "clip_001.wav").exists()
    assert updated.sample_count == 1


def test_delete_voice_clip_raises_for_missing_file(tmp_path: Path) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))

    with pytest.raises(ValueError, match="not found"):
        application.delete_voice_clip(player.id, "nope.wav")
