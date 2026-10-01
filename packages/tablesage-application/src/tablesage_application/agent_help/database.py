"""Read-only access to a workspace database for coding agents: schema text and ad-hoc queries.

Read-only is enforced by the connection (`mode=ro` plus `query_only`), not by inspecting SQL, so a write
statement fails inside SQLite instead of depending on a parser's judgment.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

# Shown separately as the database revision rather than as schema.
_MIGRATION_TABLE = "alembic_version"


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]
    total_rows: int


def connect_readonly(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA trusted_schema = OFF")
    return connection


def run_query(database: Path, sql: str, max_rows: int | None) -> QueryResult:
    """Run one statement. Keeps at most `max_rows` rows (all when None) but counts every row the query returns."""
    with closing(connect_readonly(database)) as connection:
        cursor = connection.execute(sql)
        if cursor.description is None:
            return QueryResult((), (), 0)
        columns = tuple(column[0] for column in cursor.description)
        kept: list[tuple[object, ...]] = []
        total = 0
        for row in cursor:
            total += 1
            if max_rows is None or len(kept) < max_rows:
                kept.append(tuple(row))
        return QueryResult(columns, tuple(kept), total)


def format_table(result: QueryResult, max_cell_chars: int | None) -> str:
    """An aligned plain-text table; long values end in `…(N more characters)` unless `max_cell_chars` is None."""
    if not result.columns:
        return "The statement returned no rows."
    cells = [list(result.columns), *([_cell(value, max_cell_chars) for value in row] for row in result.rows)]
    widths = [max(len(row[index]) for row in cells) for index in range(len(result.columns))]
    lines = ["  ".join(value.ljust(width) for value, width in zip(row, widths, strict=True)).rstrip() for row in cells]
    lines.insert(1, "  ".join("-" * width for width in widths))
    shown = len(result.rows)
    if shown < result.total_rows:
        lines.append(f"{shown} of {result.total_rows} rows shown; add LIMIT or narrow the query, or pass --max-rows.")
    else:
        lines.append(f"({result.total_rows} row{'' if result.total_rows == 1 else 's'})")
    return "\n".join(lines)


def schema_statements(database: Path) -> list[str]:
    """The database's own `CREATE` statements -- tables first, then indexes -- without SQLite's or the migration tool's."""
    with closing(connect_readonly(database)) as connection:
        rows = connection.execute(
            "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' AND tbl_name != ? "
            "ORDER BY type != 'table', tbl_name, name",
            (_MIGRATION_TABLE,),
        ).fetchall()
    return [row[0].strip() + ";" for row in rows]


def database_revision(database: Path) -> str | None:
    with closing(connect_readonly(database)) as connection:
        try:
            row = connection.execute(f"SELECT version_num FROM {_MIGRATION_TABLE}").fetchone()
        except sqlite3.OperationalError:
            return None
    return row[0] if row else None


def _cell(value: object, max_chars: int | None) -> str:
    if value is None:
        text = "NULL"
    elif isinstance(value, bytes):
        text = f"<{len(value)} bytes>"
    else:
        text = str(value).replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    if max_chars is not None and len(text) > max_chars:
        return f"{text[:max_chars]}…({len(text) - max_chars} more characters)"
    return text
