from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile, ZipInfo

import pytest
from sqlmodel import Session
from tablesage_application import Application
from tablesage_application.voice_clips import clips
from tablesage_model.model import Player
from tablesage_model.player_names import validate_player_name
from tablesage_tools.embeddings import Embedding


def _archive(path: Path, entries: dict[str, bytes]) -> Path:
    with ZipFile(path, "w") as archive:
        archive.writestr("players/", b"")
        for name, data in entries.items():
            archive.writestr(name, data)
    return path


def _app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Application:
    app = Application(tmp_path)

    def embed(path: Path) -> Embedding:
        if path.read_bytes() == b"bad":
            raise ValueError("unreadable audio")
        return Embedding(root=(1.0, 0.0))

    monkeypatch.setattr(app, "_embed_clip", embed)
    return app


def test_merge_new_empty_orphan_and_repeat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = _app(tmp_path, monkeypatch)
    alice = app.create_player(Player(name="Alice"))
    (tmp_path / "players/Alice/local.wav").write_bytes(b"local")
    orphan = tmp_path / "players/Bob"
    orphan.mkdir()
    (orphan / "old.txt").write_text("orphan")
    source = _archive(
        tmp_path / "players.zip",
        {
            "players/Alice/duplicate.wav": b"local",
            "players/Alice/new.wav": b"new",
            "players/Bob/clip.wav": b"bob",
            "players/Empty/": b"",
            "players/Alice/notes.txt": b"notes",
            "players/Alice/nested/clip.wav": b"ignored",
        },
    )
    with patch.object(clips, "import_voice_clips", wraps=clips.import_voice_clips) as importer:
        result = app.import_players(source)
        assert importer.call_count == 2
        assert all(call.kwargs["should_clean_audio"] is False for call in importer.call_args_list)
    assert (result.created, result.matched, result.imported_clips, result.duplicate_clips, result.ignored_entries) == (2, 1, 2, 1, 2)
    assert app.get_player(alice.id).sample_count == 2
    assert {p.name: p.sample_count for p in app.list_players()} == {"Alice": 2, "Bob": 1, "Empty": 0}
    assert not (orphan / "old.txt").exists()
    before = {p.relative_to(tmp_path / "players"): p.read_bytes() for p in (tmp_path / "players").rglob("*") if p.is_file()}
    result = app.import_players(source)
    assert result.created == result.imported_clips == 0
    assert result.duplicate_clips == 3
    assert before == {p.relative_to(tmp_path / "players"): p.read_bytes() for p in (tmp_path / "players").rglob("*") if p.is_file()}


@pytest.mark.parametrize("failure", ["embed", "commit", "install"])
def test_rollback_preserves_existing_player_and_orphan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    app = _app(tmp_path, monkeypatch)
    alice = app.create_player(Player(name="Alice"))
    (tmp_path / "players/Alice/local.wav").write_bytes(b"local")
    app.recompute_centroid(alice.id)
    before = app.get_player(alice.id).model_dump()
    orphan = tmp_path / "players/Bob"
    orphan.mkdir()
    (orphan / "precious.txt").write_bytes(b"original")
    source = _archive(
        tmp_path / "players.zip",
        {
            "players/Alice/new.wav": b"new",
            "players/Bob/import.wav": b"bad" if failure == "embed" else b"bob",
        },
    )
    if failure == "commit":
        monkeypatch.setattr(Session, "commit", lambda _: (_ for _ in ()).throw(RuntimeError("commit failure")))
    if failure == "install":
        original = Path.rename

        def rename(path: Path, target: Path) -> Path:
            if path.parent.name == "staged" and path.name == "Bob":
                raise OSError("install failure")
            return original(path, target)

        monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(ValueError, match="rolled back"):
        app.import_players(source)
    assert app.get_player(alice.id).model_dump() == before
    assert len(app.list_players()) == 1
    assert sorted(p.name for p in (tmp_path / "players/Alice").iterdir()) == ["local.wav"]
    assert (orphan / "precious.txt").read_bytes() == b"original"
    assert not list(tmp_path.glob(".player-import-*"))


def test_export_registered_only_and_empty_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = _app(tmp_path, monkeypatch)
    app.create_player(Player(name="Empty"))
    app.create_player(Player(name="Alice"))
    (tmp_path / "players/Alice/a.wav").write_bytes(b"audio")
    (tmp_path / "players/Alice/notes.txt").write_text("notes")
    (tmp_path / "players/Orphan").mkdir()
    output = tmp_path / "export.zip"
    app.export_players(output)
    with ZipFile(output) as archive:
        assert set(archive.namelist()) == {"players/", "players/Empty/", "players/Alice/", "players/Alice/a.wav", "players/Alice/notes.txt"}
    other = _app(tmp_path / "other", monkeypatch)
    result = other.import_players(output)
    assert result.created == 2
    assert result.imported_clips == 1
    assert result.ignored_entries == 1


@pytest.mark.parametrize("entry", ["../escape.wav", "players/../escape.wav", "Alice/a.wav", "players/Alice", "players/a\\b/a.wav"])
def test_rejects_unsafe_or_wrong_layout(tmp_path: Path, entry: str) -> None:
    app = Application(tmp_path)
    source = _archive(tmp_path / "bad.zip", {entry: b"bad"})
    with pytest.raises(ValueError):
        app.import_players(source)
    assert not app.list_players()


def test_symlink_archive_rejected(tmp_path: Path) -> None:
    source = tmp_path / "bad.zip"
    with ZipFile(source, "w") as archive:
        entry = ZipInfo("players/Alice/link.wav")
        entry.external_attr = 0o120777 << 16
        archive.writestr(entry, b"/etc/passwd")
    with pytest.raises(ValueError, match="Unsafe"):
        Application(tmp_path).import_players(source)


def test_empty_archive_and_case_variant_names(tmp_path: Path) -> None:
    app = Application(tmp_path)
    source = tmp_path / "empty.zip"
    app.export_players(source)
    assert app.import_players(source).created == 0
    source = _archive(source, {f"players/{name}/": b"" for name in ["Alice", "alice", " Alice "]})
    assert app.import_players(source).created == 1
    assert [player.name for player in app.list_players()] == ["Alice"]


@pytest.mark.parametrize("name", ["", " ", ".", "..", "../Alice", "a/b", "a\\b", "a\x00", "a\n", "a\x7f", "é" * 128])
def test_invalid_names_rejected_by_single_creation(tmp_path: Path, name: str) -> None:
    app = Application(tmp_path)
    with pytest.raises(ValueError):
        app.create_player(Player(name=name))
    assert app.list_players() == []


def test_byte_limit_preserves_valid_name() -> None:
    name = "é" * 127 + "a"
    assert validate_player_name(name) == name


def test_failed_export_preserves_destination(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = Application(tmp_path)
    app.create_player(Player(name="Alice"))
    (tmp_path / "players/Alice/a.wav").write_bytes(b"audio")
    output = tmp_path / "players.zip"
    output.write_bytes(b"previous export")

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(ZipFile, "write", fail)
    with pytest.raises(OSError, match="disk full"):
        app.export_players(output)
    assert output.read_bytes() == b"previous export"


def test_rejects_non_zip_and_duplicate_entries(tmp_path: Path) -> None:
    app = Application(tmp_path)
    source = tmp_path / "players.zip"
    source.write_text('{"players": ["Alice"]}')
    with pytest.raises(ValueError, match="Invalid player ZIP"):
        app.import_players(source)
    with ZipFile(source, "w") as archive:
        archive.writestr("players/Alice/a.wav", b"one")
        with pytest.warns(UserWarning, match="Duplicate"):
            archive.writestr("players/Alice/a.wav", b"two")
    with pytest.raises(ValueError, match="Duplicate archive"):
        app.import_players(source)
    assert app.list_players() == []


def test_empty_match_keeps_centroid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = _app(tmp_path, monkeypatch)
    player = app.create_player(Player(name="Alice"))
    (tmp_path / "players/Alice/a.wav").write_bytes(b"audio")
    app.recompute_centroid(player.id)
    before = app.get_player(player.id).model_dump()
    app.import_players(_archive(tmp_path / "players.zip", {"players/Alice/": b""}))
    assert app.get_player(player.id).model_dump() == before
