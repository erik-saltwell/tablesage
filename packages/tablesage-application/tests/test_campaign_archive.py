import os
import sqlite3
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import pytest
from sqlmodel import Session
from tablesage_application import Application, campaign_archive
from tablesage_model.model import Campaign, GlossaryEntry, Player
from tablesage_model.model import Session as GameSession


def _source(tmp_path: Path) -> tuple[Application, Campaign, GameSession, Path]:
    app = Application(tmp_path / "source")
    campaign = app.create_campaign(Campaign(name="Iron Pact"))
    player = app.create_player(Player(name="Alice"))
    game_session = app.create_session(campaign.id, "Opening")
    attendee = app.add_attendance(game_session.id, player.id)
    app.set_attendance_roles(game_session.id, attendee.attendance_id, ["Wizard"])
    app.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Avernus", description="A place"))
    app.create_campaign(Campaign(name="Unrelated"))
    artifact = tmp_path / "source/campaigns/Iron Pact/001/ledger.json"
    artifact.write_text('{"session_id": "' + str(game_session.id) + '"}')
    os.utime(artifact, ns=(1700000000123456789, 1700000000123456789))
    archive = tmp_path / "campaign.zip"
    app.export_campaign(campaign.id, archive)
    return app, campaign, game_session, archive


def test_roundtrip_selective_rows_uuid_mapping_and_mtimes(tmp_path: Path) -> None:
    source, campaign, game_session, archive = _source(tmp_path)
    target = Application(tmp_path / "target")
    alice = target.create_player(Player(name="Alice"))
    orphan = tmp_path / "target/campaigns/Iron Pact"
    orphan.mkdir(parents=True)
    (orphan / "old.txt").write_text("orphan")
    assert target.import_campaign(archive) == campaign.id
    assert [c.name for c in target.list_campaigns()] == ["Iron Pact"]
    assert target.get_campaign(campaign.id).model_dump() == source.get_campaign(campaign.id).model_dump()
    assert target.list_sessions(campaign.id)[0].id == game_session.id
    assert target.list_glossary_entries(campaign.id)[0].term == "Avernus"
    with sqlite3.connect(target._db_path) as database:
        assert database.execute("SELECT player_id FROM session_attendance").fetchone()[0] == alice.id.hex
        assert database.execute("SELECT count(*) FROM session_attendance_role").fetchone()[0] == 1
        assert database.execute("PRAGMA foreign_key_check").fetchall() == []
    assert not (orphan / "old.txt").exists()
    assert (orphan / "001/ledger.json").stat().st_mtime_ns == 1700000000123456789
    with ZipFile(archive) as zipped:
        snapshot = tmp_path / "snapshot.sqlite"
        snapshot.write_bytes(zipped.read("database.sqlite"))
        with sqlite3.connect(snapshot) as database:
            assert database.execute("SELECT count(*) FROM campaign").fetchone()[0] == 2


@pytest.mark.parametrize("failure", ["missing", "name", "id", "schema", "insert", "move", "commit"])
def test_failed_import_preserves_db_and_orphan(tmp_path: Path, failure: str) -> None:
    _, campaign, _, archive = _source(tmp_path)
    target = Application(tmp_path / "target")
    if failure != "missing":
        target.create_player(Player(name="Alice"))
    if failure == "name":
        target.create_campaign(Campaign(name="Iron Pact"))
    elif failure == "id":
        target.create_campaign(Campaign(id=campaign.id, name="Different"))
    if failure == "schema":
        with sqlite3.connect(target._db_path) as database:
            database.execute("UPDATE alembic_version SET version_num='different'")
    if failure == "insert":
        with sqlite3.connect(target._db_path) as database:
            database.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON session BEGIN SELECT RAISE(ABORT, 'insert failed'); END")
    orphan = tmp_path / "target/campaigns/Iron Pact"
    orphan.mkdir(parents=True, exist_ok=True)
    (orphan / "precious.txt").write_text("keep")
    before = [c.model_dump() for c in target.list_campaigns()]
    original_rename = Path.rename

    def rename(path: Path, destination: Path) -> Path:
        if failure == "move" and path.name == "Iron Pact" and path.parent.parent.name.startswith(".campaign-import-"):
            raise OSError("move failed")
        return original_rename(path, destination)

    original_connect = campaign_archive._connect

    class FailingCommit(sqlite3.Connection):
        def commit(self) -> None:
            raise sqlite3.OperationalError("commit failed")

    def connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
        if failure == "commit" and not readonly:
            connection = sqlite3.connect(path, factory=FailingCommit)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            return connection
        return original_connect(path, readonly=readonly)

    with patch.object(Path, "rename", rename), patch.object(campaign_archive, "_connect", connect), pytest.raises(ValueError):
        target.import_campaign(archive)
    assert [c.model_dump() for c in target.list_campaigns()] == before
    assert (orphan / "precious.txt").read_text() == "keep"
    assert not (orphan / "001").exists()
    with sqlite3.connect(target._db_path) as database:
        for table in ["session", "session_attendance", "session_attendance_role", "glossary_entry"]:
            assert database.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_export_processing_and_overwrite_protection(tmp_path: Path) -> None:
    source, campaign, game_session, archive = _source(tmp_path)
    previous = archive.read_bytes()
    with Session(source._engine) as session:
        row = session.get(GameSession, game_session.id)
        assert row is not None
        row.status = "processing"
        session.commit()
    with pytest.raises(ValueError, match="processing"):
        source.export_campaign(campaign.id, archive)
    assert archive.read_bytes() == previous


@pytest.mark.parametrize("entry", ["../outside", "campaigns/../outside", "campaigns/a\\b/file", "other/file"])
def test_invalid_zip_paths(tmp_path: Path, entry: str) -> None:
    target = Application(tmp_path)
    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as zipped:
        zipped.writestr("database.sqlite", b"invalid")
        zipped.writestr("campaigns/Name/", b"")
        zipped.writestr(entry, b"invalid")
    with pytest.raises(ValueError):
        target.import_campaign(archive)
    assert target.list_campaigns() == []


def test_empty_campaign_round_trip(tmp_path: Path) -> None:
    source = Application(tmp_path / "source")
    campaign = source.create_campaign(Campaign(name="Empty"))
    archive = tmp_path / "empty.zip"
    source.export_campaign(campaign.id, archive)
    target = Application(tmp_path / "target")
    assert target.import_campaign(archive) == campaign.id
