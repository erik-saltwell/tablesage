from __future__ import annotations

from pathlib import Path

import pytest
from tablesage_application import Application
from tablesage_model.model import Player


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


def test_player_folder_exists_reflects_disk_state(tmp_path: Path) -> None:
    application = Application(tmp_path)
    assert application.player_folder_exists("Alice") is False

    application.create_player(Player(name="Alice"))
    assert application.player_folder_exists("Alice") is True


def test_delete_orphan_player_folder_clears_a_stray_folder_left_by_delete(tmp_path: Path) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    application.delete_player(player.id)
    assert application.player_folder_exists("Alice") is True

    application.delete_orphan_player_folder("Alice")

    assert application.player_folder_exists("Alice") is False
    # the collision is now cleared, so re-creating with the same name succeeds
    application.create_player(Player(name="Alice"))


def test_cleanup_orphan_player_dirs_removes_only_unknown_folders(tmp_path: Path) -> None:
    application = Application(tmp_path)
    player = application.create_player(Player(name="Alice"))
    application.delete_player(player.id)
    application.create_player(Player(name="Bob"))

    removed = application.cleanup_orphan_player_dirs()

    assert removed == ["Alice"]
    assert not (tmp_path / ".tablesage" / "players" / "Alice").exists()
    assert (tmp_path / ".tablesage" / "players" / "Bob").is_dir()
