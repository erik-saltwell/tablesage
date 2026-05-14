from __future__ import annotations

from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from tablesage_model._actions.players import add_clips as add_clips_module
from tablesage_model.io import load_player
from tablesage_model.model.cast import Embedding


class FakeEmbeddingFactory:
    async def extract_async(self, audio_path: Path) -> Embedding:
        if audio_path.name == "first.wav":
            return Embedding(root=(1.0, 0.0))
        return Embedding(root=(0.0, 1.0))


def test_get_source_files_returns_sorted_top_level_wav_files(tmp_path: Path) -> None:
    clip_directory = tmp_path / "clips"
    clip_directory.mkdir()
    nested_directory = clip_directory / "nested"
    nested_directory.mkdir()
    wav_directory = clip_directory / "directory.wav"
    wav_directory.mkdir()
    second = clip_directory / "second.wav"
    first = clip_directory / "first.wav"
    second.write_bytes(b"second")
    first.write_bytes(b"first")
    (clip_directory / "ignored.mp3").write_bytes(b"ignored")
    (nested_directory / "nested.wav").write_bytes(b"nested")

    assert add_clips_module._get_source_files(clip_directory) == [first, second]


@pytest.mark.anyio
async def test_add_clips_copies_wav_files_and_saves_player(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    clip_directory = tmp_path / "clips"
    clip_directory.mkdir()
    (clip_directory / "b.wav").write_bytes(b"second")
    (clip_directory / "a.wav").write_bytes(b"first")

    filenames = iter(("first.wav", "second.wav"))
    monkeypatch.setattr(add_clips_module._paths, "generate_voice_sample_filename", lambda: next(filenames))
    monkeypatch.setattr(add_clips_module, "EmbeddingFactory", FakeEmbeddingFactory)

    await add_clips_module.add_clips("sable-crown", "ada", "Ada", clip_directory)

    player = load_player("sable-crown", "ada")
    assert player.slug == "ada"
    assert player.name == "Ada"
    assert [sample.filepath for sample in player.voice_samples] == [
        Path("voice_clips/first.wav"),
        Path("voice_clips/second.wav"),
    ]
    assert [sample.embedding for sample in player.voice_samples] == [
        Embedding(root=(1.0, 0.0)),
        Embedding(root=(0.0, 1.0)),
    ]
    assert player.centroid.root == pytest.approx((0.70710677, 0.70710677))
