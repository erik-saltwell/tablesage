"""The `tablesage` command. With no command it launches the TUI; the commands only read the current folder's workspace.

The commands exist so a coding agent launched in a workspace can read TableSage's help and inspect the workspace.
They are handled before any TUI startup work, so they never create settings, run migrations, or write logs.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path

NO_WORKSPACE_EXIT = 2
_SECTION_TITLES = {"getting-started": "Getting Started", "concepts": "Concepts", "guides": "Guides", "reference": "Reference"}


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    if args.command is None:
        from .screens.main_app import main as run_app

        run_app()
        return
    sys.exit(_run(args))


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _parser() -> argparse.ArgumentParser:
    from .agent_help import DEFAULT_MAX_CELL_CHARS, DEFAULT_MAX_ROWS

    parser = argparse.ArgumentParser(
        prog="tablesage",
        description="Run with no command to launch TableSage in the current folder. The commands below only read the "
        "workspace in the current folder; they let a coding agent answer questions about TableSage.",
    )
    commands = parser.add_subparsers(dest="command", metavar="<command>")
    commands.add_parser("report-help-topics", help="list the help topics with a one-line description of each")
    topic = commands.add_parser("output-help-topic", help="print one help topic")
    topic.add_argument("topic_id", help="a topic ID from report-help-topics, such as guides/start-a-campaign")
    commands.add_parser("report-schema", help="print the workspace database's tables, indexes, and migration revision")
    query = commands.add_parser("run-query", help="run one SQL statement over a read-only database connection")
    query.add_argument("sql", help="the SQL statement to run")
    query.add_argument("--max-rows", type=_positive_int, default=DEFAULT_MAX_ROWS, help=f"rows to print (default {DEFAULT_MAX_ROWS})")
    query.add_argument("--full-values", action="store_true", help=f"print values longer than {DEFAULT_MAX_CELL_CHARS} characters in full")
    return parser


def _run(args: argparse.Namespace) -> int:
    from tablesage_application import paths
    from tablesage_application.agent_help import agent_files_enabled, guide_is_current

    from .agent_help import app_version

    cwd = Path.cwd()
    if not paths.workspace_state_dir(cwd).is_dir():
        print(
            f"No TableSage workspace in this folder ({cwd}). Run TableSage commands from the folder you launch TableSage "
            "from, the one containing .tablesage/.",
            file=sys.stderr,
        )
        return NO_WORKSPACE_EXIT
    version = app_version()
    # Flushed so the header still comes first when stdout is piped and an error goes to stderr.
    print(f"TableSage {version} · workspace {cwd}", flush=True)
    if agent_files_enabled(cwd) and not guide_is_current(cwd, version):
        print(
            f"Warning: the workspace agent guide is missing or out of date for TableSage {version}. "
            "Continuing with the installed application's commands and public help topics. "
            "Read `tablesage output-help-topic guides/advanced-help` for current instructions.",
            file=sys.stderr,
        )
    command = {
        "report-help-topics": _report_help_topics,
        "output-help-topic": _output_help_topic,
        "report-schema": _report_schema,
        "run-query": _run_query,
    }[args.command]
    return command(cwd, args)


def _docs_directory() -> Path | None:
    from .resources import docs_directory

    directory = docs_directory()
    if directory is None:
        print("This installation of TableSage has no bundled help topics.", file=sys.stderr)
    return directory


def _report_help_topics(cwd: Path, args: argparse.Namespace) -> int:
    from tablesage_application.agent_help import list_topics

    docs = _docs_directory()
    if docs is None:
        return 1
    section: str | None = None
    for topic in list_topics(docs):
        if topic.section != section:
            section = topic.section
            print(f"\n## {_SECTION_TITLES.get(section, 'Other')}\n")
        print(f"- {topic.id}: {topic.title}. {topic.description}")
    print("\nRead a topic with: tablesage output-help-topic <topic-id>")
    return 0


def _output_help_topic(cwd: Path, args: argparse.Namespace) -> int:
    from tablesage_application.agent_help import find_topic, render_topic

    docs = _docs_directory()
    if docs is None:
        return 1
    topic = find_topic(docs, args.topic_id)
    if topic is None:
        print(f"Unknown help topic: {args.topic_id}. Run `tablesage report-help-topics` to list topics.", file=sys.stderr)
        return 2
    print(f"Help topic {topic.id}. Links written topic:<id> refer to other help topics.\n")
    print(render_topic(docs, topic), end="")
    return 0


def _database(cwd: Path) -> Path | None:
    from tablesage_application import paths

    database = paths.database_path(cwd)
    if not database.is_file():
        print("This workspace has no database yet. Launch TableSage once to create it.", file=sys.stderr)
        return None
    return database


def _report_schema(cwd: Path, args: argparse.Namespace) -> int:
    from tablesage_application.agent_help import database_revision, schema_statements
    from tablesage_application.configuration import SETTINGS_VERSION
    from tablesage_model.setup import expected_database_revision

    database = _database(cwd)
    if database is None:
        return 1
    revision, expected = database_revision(database), expected_database_revision()
    print(f"Database revision: {revision or 'none'} (this version of TableSage expects {expected})")
    print(f"Expected settings version: {SETTINGS_VERSION}")
    if revision != expected:
        print(
            "The database is not at the revision this version expects. Launching TableSage migrates an older database; "
            "a revision this version doesn't know means a newer TableSage wrote it."
        )
    print()
    print("\n\n".join(schema_statements(database)))
    return 0


def _run_query(cwd: Path, args: argparse.Namespace) -> int:
    from tablesage_application.agent_help import format_table, run_query

    from .agent_help import DEFAULT_MAX_CELL_CHARS

    database = _database(cwd)
    if database is None:
        return 1
    try:
        result = run_query(database, args.sql, args.max_rows)
    except sqlite3.Error as exc:
        hint = " run-query is read-only; make changes in TableSage itself." if "readonly" in str(exc) else ""
        print(f"Query failed: {str(exc).rstrip('.')}.{hint}", file=sys.stderr)
        return 1
    print(format_table(result, None if args.full_values else DEFAULT_MAX_CELL_CHARS))
    return 0


if __name__ == "__main__":
    main()
