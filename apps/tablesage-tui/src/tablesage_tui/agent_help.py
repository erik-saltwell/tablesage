"""Keeps a workspace's coding-agent help files current for the running version of TableSage."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
from string import Template

from tablesage_application.agent_help import AgentFilesStatus, install_agent_files
from tablesage_application.configuration import SETTINGS_VERSION

from .resources import load_resource

# `run-query`'s defaults; the agent guide quotes them.
DEFAULT_MAX_ROWS = 100
DEFAULT_MAX_CELL_CHARS = 200


def app_version() -> str:
    try:
        return metadata.version("tablesage-rpg")
    except metadata.PackageNotFoundError:
        return "0+unknown"


def agent_guide_body() -> str:
    return Template(load_resource("agent_guide.md")).substitute(
        version=app_version(),
        settings_version=SETTINGS_VERSION,
        max_rows=DEFAULT_MAX_ROWS,
        max_cell_chars=DEFAULT_MAX_CELL_CHARS,
    )


def refresh_agent_files(cwd: Path) -> AgentFilesStatus:
    return install_agent_files(cwd, app_version(), agent_guide_body())
