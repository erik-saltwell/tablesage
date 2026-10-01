from __future__ import annotations

from pathlib import Path

from tablesage_application.agent_help import AgentFilesStatus
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from ..widgets import EqualWidthButtonRow

EXAMPLE_QUESTIONS = (
    "Why can't I open Campaigns?",
    "How do I add a new Player to a Session?",
    "Why did processing stop on Session 3?",
    "What does the Ledger contain?",
)


def agent_files_message(status: AgentFilesStatus | None) -> str | None:
    """What launch did with the workspace's agent help files, in the user's terms; None when nothing was attempted."""
    if status is None:
        return None
    if not status.enabled:
        return "Agent help files are turned off: install_agent_files is false in .tablesage/settings.yaml."
    if status.error is not None:
        return f"TableSage couldn't write its agent help files: {status.error}"
    if not status.user_owned:
        return "Agent help files are ready in this folder."
    names = [stub.filename for stub in status.user_owned]
    lines = [f"TableSage left your own {' and '.join(names)} unchanged. To use its help there, add:"]
    lines += [f"  {stub.filename}: {stub.line_to_add}" for stub in status.user_owned]
    return "\n".join(lines)


class AdvancedHelpDialog(ModalScreen[None]):
    """Welcome's Advanced Help (H): how to get help from a coding agent launched in this workspace."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
    ]

    def __init__(self, workspace: Path, agent_files: AgentFilesStatus | None) -> None:
        super().__init__()
        self._workspace = workspace
        self._agent_files = agent_files

    def compose(self) -> ComposeResult:
        with Vertical(id="advanced-help-dialog") as dialog:
            dialog.border_title = "Advanced Help"
            yield Static(
                "Get help from an AI coding agent. Open a terminal in this folder and start Claude Code (claude), "
                "Codex (codex), or Gemini CLI (gemini):",
                markup=False,
            )
            yield Static(str(self._workspace), id="advanced-help-workspace", markup=False)
            yield Static(
                "TableSage sets the agent up to answer questions about the app and to look into problems in this workspace. Try asking:",
                markup=False,
            )
            yield Static("\n".join(f"• {question}" for question in EXAMPLE_QUESTIONS), id="advanced-help-examples", markup=False)
            message = agent_files_message(self._agent_files)
            if message is not None:
                yield Static(message, id="advanced-help-status", markup=False)
            yield Static(
                "The agent reads your workspace to answer, so Campaign and Session content it looks at is sent to "
                "that agent's AI provider.",
                id="advanced-help-privacy",
                markup=False,
            )
            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Close", id="advanced-help-close", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#advanced-help-close", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "advanced-help-close":
            self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
