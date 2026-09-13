"""ZIP transfer using staged folders and one database transaction.

Ordinary failures restore displaced folders. This is not crash recovery.
"""

import hashlib
import os
import shutil
import stat
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

from sqlalchemy import Engine
from sqlmodel import Session
from tablesage_model.model import Player
from tablesage_model.player_names import validate_player_name
from tablesage_model.settings import RemoveOutliersSettings
from tablesage_tools.embeddings import Embedding

from .entities import players
from .voice_clips import clips


@dataclass(frozen=True)
class PlayerArchiveResult:
    created: int = 0
    matched: int = 0
    imported_clips: int = 0
    duplicate_clips: int = 0
    ignored_entries: int = 0


def _contents(archive: ZipFile) -> tuple[dict[str, list[ZipInfo]], int]:
    folders: dict[str, list[ZipInfo]] = {}
    errors: list[str] = []
    seen: set[str] = set()
    ignored = 0
    for entry in archive.infolist():
        path = entry.filename.rstrip("/")
        parts = path.split("/")
        mode = stat.S_IFMT(entry.external_attr >> 16)
        if (
            entry.orig_filename != entry.filename
            or "\\" in path
            or any(part in {"", ".", ".."} for part in parts)
            or parts[0] != "players"
            or mode not in {0, stat.S_IFREG, stat.S_IFDIR}
        ):
            errors.append(f"Unsafe or unsupported archive entry: {entry.filename!r}")
            continue
        if path in seen:
            errors.append(f"Duplicate archive entry: {path!r}")
        seen.add(path)
        if len(parts) == 1:
            if not entry.is_dir():
                errors.append("The archive root must be the players/ directory.")
            continue
        try:
            name = validate_player_name(parts[1])
        except ValueError as exc:
            errors.append(f"{parts[1]!r}: {exc}")
            continue
        if len(parts) == 2 and not entry.is_dir():
            errors.append(f"Expected a player directory: {path!r}")
            continue
        files = folders.setdefault(name, [])
        if len(parts) == 3 and not entry.is_dir() and parts[2].endswith(".wav"):
            files.append(entry)
        elif len(parts) > 2:
            ignored += 1
    if not seen:
        errors.append("Expected an archive containing players/.")
    if errors:
        raise ValueError("Import rejected; nothing changed.\n" + "\n".join(errors))
    return folders, ignored


def _digest(path: Path) -> bytes:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").digest()


def _check_folder(folder: Path) -> None:
    if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise ValueError(f"Expected a regular player directory: {folder}")
    if folder.exists():
        for item in folder.rglob("*"):
            if item.is_symlink() or not (item.is_dir() or item.is_file()):
                raise ValueError(f"Unsupported file in player directory: {item}")


def import_players(
    engine: Engine,
    root: Path,
    source: Path,
    embed: Callable[[Path], Embedding],
    outliers: RemoveOutliersSettings,
    on_progress: Callable[[int, int], None] | None = None,
) -> PlayerArchiveResult:
    try:
        with ZipFile(source) as archive:
            folders, ignored = _contents(archive)
            return _import(engine, root, archive, folders, ignored, embed, outliers, on_progress)
    except BadZipFile as exc:
        raise ValueError(f"Invalid player ZIP archive: {exc}") from exc


def _import(
    engine: Engine,
    root: Path,
    archive: ZipFile,
    folders: dict[str, list[ZipInfo]],
    ignored: int,
    embed: Callable[[Path], Embedding],
    outliers: RemoveOutliersSettings,
    on_progress: Callable[[int, int], None] | None,
) -> PlayerArchiveResult:
    root.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=".player-import-", dir=root.parent))
    staged = workspace / "staged"
    backup = workspace / "backup"
    staged.mkdir()
    backup.mkdir()
    displaced: list[str] = []
    installed: list[str] = []
    preserve_backup = False
    created = matched = imported = duplicates = 0
    try:
        with Session(engine) as session:
            try:
                existing = {player.name: player for player in players.list_players(session)}
                for name in folders:
                    _check_folder(root / name)
                for index, (name, entries) in enumerate(sorted(folders.items()), 1):
                    destination = staged / name
                    player = existing.get(name)
                    if player is None:
                        player = players.create_player(session, Player(name=name), staged)
                        created += 1
                    else:
                        matched += 1
                        if not entries:
                            if on_progress:
                                on_progress(index, len(folders))
                            continue
                        if (root / name).exists():
                            shutil.copytree(root / name, destination)
                        else:
                            destination.mkdir()

                    hashes = {_digest(path) for path in destination.glob("*.wav") if path.is_file()}
                    incoming = workspace / "incoming" / name
                    incoming.mkdir(parents=True)
                    for entry in entries:
                        target = incoming / entry.filename.rsplit("/", 1)[1]
                        with archive.open(entry) as reader, target.open("wb") as writer:
                            shutil.copyfileobj(reader, writer)
                        digest = _digest(target)
                        if digest in hashes:
                            target.unlink()
                            duplicates += 1
                        else:
                            hashes.add(digest)
                    if any(incoming.iterdir()):
                        failed: list[str] = []

                        def checked_embed(path: Path, failures: list[str] = failed) -> Embedding:
                            try:
                                return embed(path)
                            except Exception:
                                failures.append(path.name)
                                raise

                        _, result = clips.import_voice_clips(
                            session,
                            player.id,
                            name,
                            incoming,
                            destination,
                            checked_embed,
                            min_sample_similarity=outliers.min_sample_similarity,
                            min_samples=outliers.min_samples,
                            should_clean_audio=False,
                        )
                        if result.rejected_filenames or failed:
                            filenames = result.rejected_filenames or tuple(failed)
                            raise ValueError(f"{name}: could not embed clips: {', '.join(filenames)}")
                        imported += result.imported_count
                    elif player.name in existing:
                        # Every incoming clip already exists: preserve the player verbatim.
                        shutil.rmtree(destination)
                    if on_progress:
                        on_progress(index, len(folders))

                for folder in sorted(staged.iterdir()):
                    name = folder.name
                    current = root / name
                    if current.exists():
                        current.rename(backup / name)
                        displaced.append(name)
                    folder.rename(current)
                    installed.append(name)
                session.commit()
            except Exception as exc:
                session.rollback()
                recovery_errors: list[str] = []
                for name in reversed(installed):
                    try:
                        shutil.rmtree(root / name)
                    except OSError as error:
                        recovery_errors.append(f"{name}: {error}")
                for name in reversed(displaced):
                    try:
                        (backup / name).rename(root / name)
                    except OSError as error:
                        recovery_errors.append(f"{name}: {error}")
                if recovery_errors:
                    preserve_backup = True
                    raise ValueError(
                        f"Import failed: {exc}. Recovery incomplete; backups retained at {backup}:\n" + "\n".join(recovery_errors)
                    ) from exc
                raise ValueError(f"Import failed; all changes rolled back: {exc}") from exc
        return PlayerArchiveResult(created, matched, imported, duplicates, ignored)
    finally:
        if not preserve_backup:
            shutil.rmtree(workspace)


def export_players(root: Path, names: list[str], destination: Path) -> None:
    if destination.resolve().is_relative_to(root.resolve()):
        raise ValueError("Choose an export location outside the players directory.")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("players/", b"")
            for name in sorted(names):
                validate_player_name(name)
                folder = root / name
                _check_folder(folder)
                archive.writestr(f"players/{name}/", b"")
                if folder.exists():
                    for item in sorted(folder.rglob("*")):
                        archive.write(item, f"players/{name}/{item.relative_to(folder).as_posix()}")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
