from __future__ import annotations

from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from tablesage_model import _paths
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


class _DeterministicEmbeddingFactory:
    async def extract_async(self, audio_path: Path) -> Embedding:
        seed = float(sum(audio_path.stem.encode("utf-8")) % 100) / 100.0
        return Embedding(root=(seed, 1.0 - seed))


def _seed_campaign() -> None:
    from tablesage_model.io import save_campaign, save_player_set
    from tablesage_model.model.campaign import Campaign
    from tablesage_model.model.cast import PlayerName, PlayerSet

    save_campaign(Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada"))
    save_player_set("sable-crown", PlayerSet(players=(PlayerName(slug="ada", name="Ada"),)))


def _write_wavs(directory: Path, *names: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / name).write_bytes(b"FAKE-WAV-" + name.encode("utf-8"))


@pytest.mark.anyio
async def test_add_clips_from_a_second_directory_accumulates_with_first_directorys_samples(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _seed_campaign()
    monkeypatch.setattr(add_clips_module, "EmbeddingFactory", _DeterministicEmbeddingFactory)

    dir_one = tmp_path / "one"
    dir_two = tmp_path / "two"
    _write_wavs(dir_one, "a.wav", "b.wav")
    _write_wavs(dir_two, "c.wav")

    await add_clips_module.add_clips("sable-crown", "ada", "Ada", dir_one)
    await add_clips_module.add_clips("sable-crown", "ada", "Ada", dir_two)

    final = load_player("sable-crown", "ada")
    sources = {sample.source for sample in final.voice_samples}
    assert sources == {str(dir_one.resolve()), str(dir_two.resolve())}
    assert len(final.voice_samples) == 3


@pytest.mark.anyio
async def test_add_clips_twice_on_same_directory_replaces_only_that_sources_samples(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    from tablesage_model.model.cast import ProvenanceType

    _seed_campaign()
    monkeypatch.setattr(add_clips_module, "EmbeddingFactory", _DeterministicEmbeddingFactory)

    other_dir = tmp_path / "other"
    target_dir = tmp_path / "target"
    _write_wavs(other_dir, "x.wav")
    _write_wavs(target_dir, "first-a.wav", "first-b.wav")

    await add_clips_module.add_clips("sable-crown", "ada", "Ada", other_dir)
    await add_clips_module.add_clips("sable-crown", "ada", "Ada", target_dir)
    after_two_imports = load_player("sable-crown", "ada")
    assert len(after_two_imports.voice_samples) == 3

    # Update target_dir's contents and re-import — only target_dir's prior samples should be retracted.
    for path in target_dir.glob("*.wav"):
        path.unlink()
    _write_wavs(target_dir, "second-a.wav", "second-b.wav", "second-c.wav")
    await add_clips_module.add_clips("sable-crown", "ada", "Ada", target_dir)

    final = load_player("sable-crown", "ada")
    by_source: dict[str, list] = {}
    for sample in final.voice_samples:
        by_source.setdefault(sample.source, []).append(sample)
    assert len(by_source[str(other_dir.resolve())]) == 1
    assert len(by_source[str(target_dir.resolve())]) == 3
    assert all(s.provenance_type == ProvenanceType.IMPORT for s in final.voice_samples)


@pytest.mark.anyio
async def test_add_clips_re_import_deletes_backing_wavs_of_retracted_samples(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _seed_campaign()
    monkeypatch.setattr(add_clips_module, "EmbeddingFactory", _DeterministicEmbeddingFactory)

    target_dir = tmp_path / "clips"
    _write_wavs(target_dir, "alpha.wav", "beta.wav")
    await add_clips_module.add_clips("sable-crown", "ada", "Ada", target_dir)

    first_call_player = load_player("sable-crown", "ada")
    player_root = _paths.player_dir("sable-crown", "ada")
    first_call_backing_wavs = [player_root / sample.filepath for sample in first_call_player.voice_samples]
    assert all(path.exists() for path in first_call_backing_wavs)

    for path in target_dir.glob("*.wav"):
        path.unlink()
    _write_wavs(target_dir, "gamma.wav")
    await add_clips_module.add_clips("sable-crown", "ada", "Ada", target_dir)

    for path in first_call_backing_wavs:
        assert not path.exists(), f"expected retracted backing wav to be deleted: {path}"


@pytest.mark.anyio
async def test_add_clips_default_path_copies_raw_bytes_into_voice_clips_dir(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _seed_campaign()
    monkeypatch.setattr(add_clips_module, "EmbeddingFactory", _DeterministicEmbeddingFactory)

    clip_dir = tmp_path / "clips"
    clip_dir.mkdir()
    raw_bytes = b"RAW-AUDIO-CONTENT-DO-NOT-CLEAN"
    (clip_dir / "alpha.wav").write_bytes(raw_bytes)

    await add_clips_module.add_clips("sable-crown", "ada", "Ada", clip_dir)

    final = load_player("sable-crown", "ada")
    target_path = _paths.player_dir("sable-crown", "ada") / final.voice_samples[0].filepath
    assert target_path.read_bytes() == raw_bytes


@pytest.mark.anyio
async def test_add_clips_with_clean_clips_writes_cleaned_bytes_into_voice_clips_dir(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _seed_campaign()
    monkeypatch.setattr(add_clips_module, "EmbeddingFactory", _DeterministicEmbeddingFactory)

    async def fake_clean_clip(source: Path, target: Path, *, normalize: bool = False) -> None:
        assert normalize is False, "per-clip cleaning should always be normalize=False"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"CLEANED-" + source.read_bytes())

    monkeypatch.setattr(add_clips_module, "clean_clip", fake_clean_clip)

    clip_dir = tmp_path / "clips"
    clip_dir.mkdir()
    raw_bytes = b"RAW-AUDIO-CONTENT"
    (clip_dir / "alpha.wav").write_bytes(raw_bytes)

    await add_clips_module.add_clips("sable-crown", "ada", "Ada", clip_dir, clean_clips=True)

    final = load_player("sable-crown", "ada")
    target_path = _paths.player_dir("sable-crown", "ada") / final.voice_samples[0].filepath
    assert target_path.read_bytes() == b"CLEANED-" + raw_bytes
