from __future__ import annotations

import sqlite3
from pathlib import Path

import sqlalchemy
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, event

from .._paths import resolve_database_path

_MIGRATIONS_DIR = Path(__file__).parent.parent / "_migrations"


def ensure_database(cwd: Path | None = None) -> Path:
    db_path: Path = resolve_database_path(cwd)
    config = Config()
    config.set_main_option("script_location", str(_MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(config, "head")
    return db_path


def expected_database_revision() -> str | None:
    """The migration revision this version of TableSage upgrades a workspace database to; reads no database."""
    config = Config()
    config.set_main_option("script_location", str(_MIGRATIONS_DIR))
    return ScriptDirectory.from_config(config).get_current_head()


def create_engine(db_path: Path) -> Engine:
    engine = sqlalchemy.create_engine(f"sqlite:///{db_path}")

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection: sqlite3.Connection, connection_record: object) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine
