from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import ProgressBar, Static


class ProgressDialog(ModalScreen[None]):
    """A cancel-less modal progress indicator.

    Shows an indeterminate progress bar plus a status message while the
    caller runs work on a background thread worker. The caller is
    responsible for popping this screen once that work finishes (success or
    error) -- there is no button or binding that dismisses it on its own.
    """

    def __init__(self, *, title: str, message: str) -> None:
        super().__init__()
        self._title = title
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="progress-dialog") as dialog:
            dialog.border_title = self._title
            yield Static(self._message, id="progress-message")
            yield ProgressBar(id="progress-bar", show_eta=False)

    def update_message(self, message: str) -> None:
        self.query_one("#progress-message", Static).update(message)

    def set_progress(self, completed: int, total: int) -> None:
        """Switch the bar from indeterminate to a determinate completed/total display."""
        self.query_one("#progress-bar", ProgressBar).update(total=total, progress=completed)
