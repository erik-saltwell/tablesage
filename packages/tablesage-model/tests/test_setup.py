from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlmodel import Session, create_engine, select
from tablesage_model import setup
from tablesage_model.model import Campaign


def _current_revision(db_path: Path) -> str:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    finally:
        conn.close()


def test_ensure_database_creates_and_migrates_fresh_directory(tmp_path: Path) -> None:
    db_path = setup.ensure_database(tmp_path)

    assert db_path == tmp_path / ".tablesage" / "tablesage.db"
    assert db_path.exists()

    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        session.add(Campaign(name="Iron Pact"))
        session.commit()

        stored = session.exec(select(Campaign)).one()

    assert stored.name == "Iron Pact"


def test_ensure_database_is_a_noop_when_already_at_head(tmp_path: Path) -> None:
    first_path = setup.ensure_database(tmp_path)
    revision_after_first_run = _current_revision(first_path)

    second_path = setup.ensure_database(tmp_path)
    revision_after_second_run = _current_revision(second_path)

    assert first_path == second_path
    assert revision_after_first_run == revision_after_second_run

    engine = create_engine(f"sqlite:///{second_path}")
    with Session(engine) as session:
        session.add(Campaign(name="Second Run Campaign"))
        session.commit()

        stored = session.exec(select(Campaign)).one()

    assert stored.name == "Second Run Campaign"
