"""The files that let a coding agent (Claude Code, Codex, Gemini CLI) launched in a workspace help with TableSage.

TableSage owns `.tablesage/agent-guide.md` and rewrites it whenever the version recorded in it differs from the
running app's. The workspace-root `CLAUDE.md`, `GEMINI.md`, and `AGENTS.md` are stubs that point at the guide:
created when missing, never rewritten (so anything the user adds to them survives), and never touched at all when
the user's own file -- one without the TableSage marker -- is already there.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml

from .. import paths
from ..configuration import atomic_write

GUIDE_FILENAME = "agent-guide.md"
MANAGED_MARKER = "<!-- tablesage-managed"
_VERSION_PATTERN = re.compile(r"<!-- tablesage-agent-guide version: (\S+) -->")
_STUB_HEADER = (
    "<!-- tablesage-managed: TableSage created this file for coding agents. It never rewrites it, so your own additions "
    "are kept. To opt out, set install_agent_files: false in .tablesage/settings.yaml, then delete this file. -->\n"
)
_IMPORT_LINE = f"@.tablesage/{GUIDE_FILENAME}"
_READ_GUIDE_LINE = f"Before answering any question about TableSage or this workspace, read `.tablesage/{GUIDE_FILENAME}` and follow it."
# Codex has no import syntax, so AGENTS.md asks the agent to read the guide; Claude Code and Gemini CLI import it.
_STUBS: tuple[tuple[str, str], ...] = (
    ("CLAUDE.md", _IMPORT_LINE),
    ("GEMINI.md", _IMPORT_LINE),
    ("AGENTS.md", _READ_GUIDE_LINE),
)


class StubState(Enum):
    CREATED = "created"
    MANAGED = "managed"
    USER_OWNED = "user_owned"


@dataclass(frozen=True)
class StubResult:
    filename: str
    state: StubState
    # What to add to the user's own file so it picks up the guide.
    line_to_add: str


@dataclass(frozen=True)
class AgentFilesStatus:
    enabled: bool
    stubs: tuple[StubResult, ...] = ()
    error: str | None = None

    @property
    def user_owned(self) -> tuple[StubResult, ...]:
        return tuple(stub for stub in self.stubs if stub.state is StubState.USER_OWNED)


def guide_path(cwd: Path) -> Path:
    return paths.workspace_state_dir(cwd) / GUIDE_FILENAME


def version_line(version: str) -> str:
    return f"<!-- tablesage-agent-guide version: {version} -->"


def installed_guide_version(cwd: Path) -> str | None:
    try:
        match = _VERSION_PATTERN.search(guide_path(cwd).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    return match.group(1) if match else None


def guide_is_current(cwd: Path, version: str) -> bool:
    """Stale means missing, without a readable version, or written by a different (newer or older) version."""
    return installed_guide_version(cwd) == version


def agent_files_enabled(cwd: Path) -> bool:
    """Read `install_agent_files` leniently, before settings are loaded: only an explicit `false` turns it off.

    A missing, unreadable, or invalid settings file means on, so a broken settings file -- a likely reason to want
    help -- never stops the agent files from being installed.
    """
    try:
        data = yaml.safe_load(paths.settings_path(cwd).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return True
    return not (isinstance(data, dict) and data.get("install_agent_files") is False)


def install_agent_files(cwd: Path, version: str, guide_body: str) -> AgentFilesStatus:
    """Refresh the guide if it is stale and create any missing stubs. Never raises for file-system errors."""
    if not agent_files_enabled(cwd):
        return AgentFilesStatus(enabled=False)
    try:
        if not guide_is_current(cwd, version):
            atomic_write(guide_path(cwd), f"{version_line(version)}\n{guide_body}")
        return AgentFilesStatus(enabled=True, stubs=tuple(_ensure_stub(cwd / filename, line) for filename, line in _STUBS))
    except OSError as exc:
        return AgentFilesStatus(enabled=True, error=str(exc))


def _ensure_stub(path: Path, line: str) -> StubResult:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(f"{_STUB_HEADER}\n{line}\n")
        return StubResult(path.name, StubState.CREATED, line)
    except FileExistsError:
        pass
    # On case-insensitive file systems a user's `claude.md` lands here too, and is left alone as their own.
    text = path.read_text(encoding="utf-8", errors="replace")
    return StubResult(path.name, StubState.MANAGED if MANAGED_MARKER in text else StubState.USER_OWNED, line)
