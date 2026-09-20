"""Campaign ZIP transfer with a complete SQLite snapshot and selective import."""

import os
import shutil
import sqlite3
import stat
import struct
import tempfile
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

from tablesage_model.player_names import validate_player_name

_TABLES = ("campaign", "glossary_entry", "session", "session_attendance", "session_attendance_role")
_MTIME_TAG = 0x5453


def _connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    connection = sqlite3.connect(path.as_uri() + ("?mode=ro" if readonly else "?mode=rw"), uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA trusted_schema=OFF")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def _check_tree(folder: Path) -> None:
    for item in [folder, *folder.rglob("*")]:
        if item.is_symlink() or not (item.is_file() or item.is_dir()):
            raise ValueError(f"Unsupported campaign path: {item}")


def export_campaign(database: Path, root: Path, campaign_id: uuid.UUID, destination: Path) -> None:
    temporary: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="tablesage-campaign-export-") as directory:
            snapshot = Path(directory) / "database.sqlite"
            with closing(_connect(database.resolve(), readonly=True)) as source, closing(sqlite3.connect(snapshot)) as target:
                source.backup(target)
            with closing(_connect(snapshot, readonly=True)) as connection:
                campaign = connection.execute("SELECT * FROM campaign WHERE id=?", (campaign_id.hex,)).fetchone()
                if campaign is None:
                    raise ValueError("Campaign not found.")
                name = validate_player_name(campaign["name"])
                if connection.execute("SELECT 1 FROM session WHERE campaign_id=? AND status='processing'", (campaign_id.hex,)).fetchone():
                    raise ValueError("Wait for campaign session processing to finish before exporting.")
            folder = root / name
            if not folder.is_dir():
                raise ValueError(f"Campaign folder is missing: {folder}")
            _check_tree(folder)
            if destination.resolve().is_relative_to(folder.resolve()):
                raise ValueError("Choose an export location outside the campaign folder.")
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name)
            with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as archive:
                archive.write(snapshot, "database.sqlite")
                for item in [folder, *sorted(folder.rglob("*"))]:
                    relative = item.relative_to(root).as_posix()
                    info = ZipInfo.from_file(item, f"campaigns/{relative}", strict_timestamps=False)
                    info.compress_type = ZIP_DEFLATED
                    # Preserve nanoseconds: artifact freshness compares file mtimes to DB timestamps.
                    info.extra = struct.pack("<HHq", _MTIME_TAG, 8, item.stat().st_mtime_ns)
                    if item.is_dir():
                        archive.writestr(info, b"")
                    else:
                        with item.open("rb") as reader, archive.open(info, "w", force_zip64=True) as writer:
                            shutil.copyfileobj(reader, writer)
            os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _mtime(entry: ZipInfo) -> int:
    extra = entry.extra
    while len(extra) >= 4:
        tag, length = struct.unpack("<HH", extra[:4])
        if tag == _MTIME_TAG and length == 8 and len(extra) >= 12:
            return struct.unpack("<q", extra[4:12])[0]
        extra = extra[4 + length :]
    return int(datetime(*entry.date_time).timestamp() * 1_000_000_000)


def _extract(source: Path, workspace: Path) -> str:
    with ZipFile(source) as archive:
        names: set[str] = set()
        seen: set[str] = set()
        errors: list[str] = []
        for entry in archive.infolist():
            path = entry.filename.rstrip("/")
            parts = path.split("/")
            mode = stat.S_IFMT(entry.external_attr >> 16)
            if (
                entry.orig_filename != entry.filename
                or "\\" in path
                or any(part in {"", ".", ".."} for part in parts)
                or mode not in {0, stat.S_IFDIR, stat.S_IFREG}
                or path in seen
            ):
                errors.append(f"Unsafe or duplicate ZIP entry: {entry.filename!r}")
                continue
            seen.add(path)
            if path == "database.sqlite" and not entry.is_dir():
                continue
            if parts[0] != "campaigns" or (len(parts) < 3 and not entry.is_dir()):
                errors.append(f"Unexpected ZIP entry: {entry.filename!r}")
                continue
            if len(parts) >= 2:
                try:
                    names.add(validate_player_name(parts[1]))
                except ValueError as exc:
                    errors.append(f"Invalid campaign name: {exc}")
        if "database.sqlite" not in seen or len(names) != 1:
            errors.append("Expected database.sqlite and exactly one campaigns/<campaign name>/ directory.")
        if errors:
            raise ValueError("\n".join(errors))
        for entry in archive.infolist():
            target = workspace / entry.filename
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as reader, target.open("wb") as writer:
                    shutil.copyfileobj(reader, writer)
                timestamp = _mtime(entry)
                os.utime(target, ns=(timestamp, timestamp))
        return names.pop()


def _rows(connection: sqlite3.Connection, table: str, predicate: str, value: str) -> list[dict]:
    return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" WHERE {predicate}', (value,))]


def _merge(source: sqlite3.Connection, target: sqlite3.Connection, name: str) -> uuid.UUID:
    source_version = [tuple(row) for row in source.execute("SELECT version_num FROM alembic_version ORDER BY version_num")]
    target_version = [tuple(row) for row in target.execute("SELECT version_num FROM alembic_version ORDER BY version_num")]
    if source_version != target_version:
        raise ValueError(f"Database schema versions differ: archive={source_version}, local={target_version}.")
    for table in (*_TABLES, "player"):
        if [tuple(row) for row in source.execute(f'PRAGMA table_info("{table}")')] != [
            tuple(row) for row in target.execute(f'PRAGMA table_info("{table}")')
        ]:
            raise ValueError(f"Database schema differs for {table}.")
    if target.execute("SELECT 1 FROM campaign WHERE name=?", (name,)).fetchone():
        raise ValueError(f"A campaign named {name!r} already exists.")
    campaign = _rows(source, "campaign", "name=?", name)
    if len(campaign) != 1:
        raise ValueError("Campaign folder does not match a campaign in the database snapshot.")
    campaign_id = campaign[0]["id"]
    records = {
        "campaign": campaign,
        "glossary_entry": _rows(source, "glossary_entry", "campaign_id=?", campaign_id),
        "session": _rows(source, "session", "campaign_id=?", campaign_id),
        "session_attendance": _rows(
            source, "session_attendance", "session_id IN (SELECT id FROM session WHERE campaign_id=?)", campaign_id
        ),
        "session_attendance_role": _rows(
            source,
            "session_attendance_role",
            "attendance_id IN (SELECT id FROM session_attendance WHERE session_id IN (SELECT id FROM session WHERE campaign_id=?))",
            campaign_id,
        ),
    }
    local_players = {row["name"]: row["id"] for row in target.execute("SELECT id, name FROM player")}
    archived_players = {row["id"]: row["name"] for row in source.execute("SELECT id, name FROM player")}
    errors: list[str] = []
    for row in records["session_attendance"]:
        player_name = archived_players.get(row["player_id"])
        if player_name not in local_players:
            errors.append(f"Missing player: {player_name or row['player_id']}")
        else:
            row["player_id"] = local_players[player_name]
    for table, rows in records.items():
        for row in rows:
            if target.execute(f'SELECT 1 FROM "{table}" WHERE id=?', (row["id"],)).fetchone():
                errors.append(f"Conflicting {table} ID: {row['id']}")
    if errors:
        raise ValueError("\n".join(sorted(set(errors))))
    for table, rows in records.items():
        for row in rows:
            columns = ", ".join(f'"{column}"' for column in row)
            parameters = ", ".join("?" for _ in row)
            target.execute(f'INSERT INTO "{table}" ({columns}) VALUES ({parameters})', tuple(row.values()))
    return uuid.UUID(campaign_id)


def import_campaign(database: Path, root: Path, source: Path) -> uuid.UUID:
    root.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=".campaign-import-", dir=root.parent))
    backup = workspace / "orphan"
    destination: Path | None = None
    installed = False
    preserve_backup = False
    try:
        name = _extract(source, workspace)
        destination = root / name
        if destination.exists() or destination.is_symlink():
            if not destination.is_dir():
                raise ValueError(f"Destination is not a campaign directory: {destination}")
            _check_tree(destination)
        with closing(_connect(workspace / "database.sqlite", readonly=True)) as snapshot, closing(_connect(database.resolve())) as target:
            target.execute("BEGIN IMMEDIATE")
            try:
                campaign_id = _merge(snapshot, target, name)
                if destination.exists():
                    destination.rename(backup)
                (workspace / "campaigns" / name).rename(destination)
                installed = True
                target.commit()
            except Exception:
                target.rollback()
                raise
        return campaign_id
    except Exception as exc:
        try:
            if installed and destination is not None:
                shutil.rmtree(destination)
            if backup.exists() and destination is not None:
                backup.rename(destination)
        except OSError as recovery_error:
            preserve_backup = True
            raise ValueError(f"Import failed: {exc}. Recovery failed: {recovery_error}. Backup retained at {backup}.") from exc
        if isinstance(exc, (sqlite3.Error, BadZipFile, OSError, ValueError)):
            raise ValueError(f"Import failed; all changes rolled back: {exc}") from exc
        raise
    finally:
        if not preserve_backup:
            shutil.rmtree(workspace)
