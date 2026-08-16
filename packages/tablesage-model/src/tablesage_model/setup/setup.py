from __future__ import annotations

from pathlib import Path

import sqlalchemy
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine

from .._paths import resolve_database_path


def ensure_database(cwd: Path | None = None) -> Path:
    db_path: Path = resolve_database_path(cwd)
    migrations_dir = Path(__file__).parent.parent / "_migrations"
    config = Config()
    config.set_main_option("script_location", str(migrations_dir))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(config, "head")
    return db_path


def create_engine(db_path: Path) -> Engine:
    return sqlalchemy.create_engine(f"sqlite:///{db_path}")
