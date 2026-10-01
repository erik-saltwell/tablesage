"""Help for coding agents launched in a workspace: their context files, bundled help topics, and read-only data access."""

from .agent_files import (
    GUIDE_FILENAME,
    AgentFilesStatus,
    StubResult,
    StubState,
    agent_files_enabled,
    guide_is_current,
    guide_path,
    install_agent_files,
    installed_guide_version,
)
from .database import QueryResult, database_revision, format_table, run_query, schema_statements
from .help_topics import SECTION_ORDER, HelpTopic, find_topic, list_topics, render_topic

__all__ = [
    "GUIDE_FILENAME",
    "SECTION_ORDER",
    "AgentFilesStatus",
    "HelpTopic",
    "QueryResult",
    "StubResult",
    "StubState",
    "agent_files_enabled",
    "database_revision",
    "find_topic",
    "format_table",
    "guide_is_current",
    "guide_path",
    "install_agent_files",
    "installed_guide_version",
    "list_topics",
    "render_topic",
    "run_query",
    "schema_statements",
]
