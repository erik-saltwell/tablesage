from __future__ import annotations

import wave
from pathlib import Path

import pytest
from tablesage_application import Application
from tablesage_application.voice_clips.clips import VoiceClip, find_clips_by_hash_segment, hash8
from tablesage_model.model import Player
from tablesage_model.settings import AppSettings, RemoveOutliersSettings
from tablesage_tools.embeddings import Embedding


def _write_wav(path: Path, *, num_frames: int = 16000, framerate: int = 16000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(framerate)
        wav_file.writeframes(b"\x00\x00" * num_frames)


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
    _write_wav(folder / "clip_001.wav", num_frames=16000)
    _write_wav(folder / "clip_002.wav", num_frames=8000)

    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    updated = application.recompute_centroid(player.id)

    assert updated.sample_count == 2
    assert updated.embedding_dimension == 2
    assert updated.centroid_embedding is not None
    assert updated.computed_at is not None


def test_recompute_centroid_reports_progress_per_clip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    _write_wav(folder / "clip_001.wav", num_frames=16000)
    _write_wav(folder / "clip_002.wav", num_frames=8000)
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    progress_calls: list[tuple[int, int]] = []
    application.recompute_centroid(player.id, lambda completed, total: progress_calls.append((completed, total)))

    assert progress_calls == [(1, 2), (2, 2)]


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


def test_cleanup_voice_clips_deletes_duplicate_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    _write_wav(folder / "clip_001.wav")
    _write_wav(folder / "clip_002.wav")  # identical bytes to clip_001 -> duplicate
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    updated, deleted = application.cleanup_voice_clips(player.id)

    assert deleted == ["clip_002.wav"]
    assert not (folder / "clip_002.wav").exists()
    assert (folder / "clip_001.wav").exists()
    assert updated.sample_count == 1


def test_cleanup_voice_clips_reports_nothing_deleted_when_all_unique(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    _write_wav(folder / "clip_001.wav", num_frames=16000)
    _write_wav(folder / "clip_002.wav", num_frames=8000)
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    updated, deleted = application.cleanup_voice_clips(player.id)

    assert deleted == []
    assert updated.sample_count == 2


def test_cleanup_voice_clips_uses_injected_settings_for_outlier_threshold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = AppSettings(remove_outliers=RemoveOutliersSettings(min_sample_similarity=0.99, min_samples=1))
    application = Application(tmp_path, settings=settings)
    player = application.create_player(Player(name="Alice"))
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    _write_wav(folder / "clip_001.wav", num_frames=16000)
    _write_wav(folder / "clip_002.wav", num_frames=8000)
    _write_wav(folder / "clip_003.wav", num_frames=4000)

    embeddings = {
        folder / "clip_001.wav": Embedding(root=(1.0, 0.0)),
        folder / "clip_002.wav": Embedding(root=(1.0, 0.0)),
        folder / "clip_003.wav": Embedding(root=(0.0, 1.0)),
    }
    monkeypatch.setattr(application, "_embed_clip", lambda path: embeddings[path])

    updated, deleted = application.cleanup_voice_clips(player.id)

    assert deleted == ["clip_003.wav"]
    assert not (folder / "clip_003.wav").exists()
    assert updated.sample_count == 2


def test_validate_import_source_raises_for_missing_wav(tmp_path: Path) -> None:
    application = Application(tmp_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "notes.txt").write_text("not a clip")

    with pytest.raises(ValueError, match="no .wav files"):
        application.validate_import_source(source_dir)


def test_validate_import_source_raises_for_non_directory(tmp_path: Path) -> None:
    application = Application(tmp_path)
    source_file = tmp_path / "clip.wav"
    _write_wav(source_file)

    with pytest.raises(ValueError, match="not a directory"):
        application.validate_import_source(source_file)


def test_import_voice_clips_copies_and_embeds_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    source_dir = tmp_path / "source"
    _write_wav(source_dir / "a.wav", num_frames=16000)
    _write_wav(source_dir / "b.wav", num_frames=8000)
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    updated, result = application.import_voice_clips(player.id, source_dir)

    assert result.imported_count == 2
    assert result.replaced_count == 0
    assert result.rejected_filenames == ()
    assert updated.sample_count == 2

    folder = tmp_path / ".tablesage" / "players" / "Alice"
    imported_names = [path.name for path in folder.glob("import-*.wav")]
    assert len(imported_names) == 2
    assert all(name.startswith("import-alice-") for name in imported_names)


def test_import_voice_clips_reports_progress_per_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    source_dir = tmp_path / "source"
    _write_wav(source_dir / "a.wav")
    _write_wav(source_dir / "b.wav")
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    progress_calls: list[tuple[int, int]] = []
    application.import_voice_clips(player.id, source_dir, lambda completed, total: progress_calls.append((completed, total)))

    assert progress_calls == [(1, 2), (2, 2)]


def test_import_voice_clips_skips_files_that_fail_to_embed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    source_dir = tmp_path / "source"
    _write_wav(source_dir / "good.wav", num_frames=16000)
    _write_wav(source_dir / "bad.wav", num_frames=8000)

    def embed(path: Path) -> Embedding:
        with wave.open(str(path), "rb") as wav_file:
            if wav_file.getnframes() == 8000:
                raise RuntimeError("bad")
        return Embedding(root=(1.0, 0.0))

    monkeypatch.setattr(application, "_embed_clip", embed)

    updated, result = application.import_voice_clips(player.id, source_dir)

    assert result.imported_count == 1
    assert result.rejected_filenames == ("bad.wav",)
    assert updated.sample_count == 1

    folder = tmp_path / ".tablesage" / "players" / "Alice"
    # only one clip should remain on disk -- the rejected copy was cleaned up
    assert len(list(folder.glob("import-*.wav"))) == 1


def test_import_voice_clips_replaces_prior_import_of_same_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    source_dir = tmp_path / "source"
    _write_wav(source_dir / "a.wav", num_frames=16000)
    _write_wav(source_dir / "b.wav", num_frames=8000)
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    application.import_voice_clips(player.id, source_dir)
    folder = tmp_path / ".tablesage" / "players" / "Alice"
    first_import_names = {path.name for path in folder.glob("import-*.wav")}

    # simulate an updated source directory (one clip removed, a new one added)
    (source_dir / "a.wav").unlink()
    _write_wav(source_dir / "c.wav", num_frames=4000)

    updated, result = application.import_voice_clips(player.id, source_dir)

    assert result.replaced_count == 2
    assert result.imported_count == 2
    assert updated.sample_count == 2

    second_import_names = {path.name for path in folder.glob("import-*.wav")}
    assert first_import_names.isdisjoint(second_import_names)


def test_find_prior_import_clips_survives_player_rename(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    source_dir = tmp_path / "source"
    _write_wav(source_dir / "a.wav")
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))
    application.import_voice_clips(player.id, source_dir)

    application.rename_player(player.id, "Alicia")

    matches = application.find_prior_import_clips(player.id, source_dir)
    assert len(matches) == 1


def test_find_clips_by_hash_segment_matches_only_the_given_prefix_and_hash(tmp_path: Path) -> None:
    folder = tmp_path / "player"
    session_hash = hash8("session-id-a")
    other_hash = hash8("session-id-b")
    _write_wav(folder / f"session-alice-iron-pact-one-{session_hash}-{'a' * 32}.wav")
    _write_wav(folder / f"session-alice-iron-pact-one-{other_hash}-{'b' * 32}.wav")
    _write_wav(folder / f"import-alice-{session_hash}-{'c' * 32}.wav")

    matches = find_clips_by_hash_segment(folder, "session", session_hash)

    assert [path.name for path in matches] == [f"session-alice-iron-pact-one-{session_hash}-{'a' * 32}.wav"]


def test_import_voice_clips_first_time_has_no_replacements(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    source_dir = tmp_path / "source"
    _write_wav(source_dir / "a.wav")
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    matches_before = application.find_prior_import_clips(player.id, source_dir)
    assert matches_before == []

    _updated, result = application.import_voice_clips(player.id, source_dir)
    assert result.replaced_count == 0
