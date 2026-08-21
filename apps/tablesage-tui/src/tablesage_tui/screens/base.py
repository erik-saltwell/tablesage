from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

from tablesage_application import Application
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer
from textual.worker import Worker, WorkerState

from ..dialogs.progress import ProgressDialog
from ..widgets.tablesage_header import TableSageHeader

if TYPE_CHECKING:
    from .main_app import TableSageApp

_PROGRESS_WORKER_GROUP = "tablesage-progress"

ResultT = TypeVar("ResultT")


class TableSageScreen(Screen[None]):
    """Shared chrome for full-page TableSage screens."""

    section = ""
    campaign = "no campaign loaded"

    # Merged with each subclass's own BINDINGS (Textual combines BINDINGS across
    # the whole MRO), so every screen gets F5 without redeclaring it.
    BINDINGS = [
        Binding("f5", "refresh_screen", "Refresh", key_display="F5", show=False),
    ]

    _progress_on_success: Callable[[Any], None] | None = None
    _progress_dialog: ProgressDialog | None = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="app-frame surface-1"):
            yield TableSageHeader(
                section=self.section,
                campaign=self.campaign,
            )

            with Vertical(classes="screen-body"):
                yield from self.compose_content()

            yield Footer()

    def compose_content(self) -> ComposeResult:
        """Supply the content unique to a particular screen."""
        yield from ()

    @property
    def application(self) -> Application:
        return cast("TableSageApp", self.app).application

    def action_pop_screen(self) -> None:
        """Pop back to the previous screen. Subclasses opt in via an `escape` binding."""
        self.app.pop_screen()

    def action_refresh_screen(self) -> None:
        """Reload this screen's data from the DB/disk -- for changes made outside the app."""
        self.refresh_data()

    def refresh_data(self) -> None:
        """Reload the data this screen displays. No-op by default; override in screens that show live data."""

    def run_with_progress(self, *, title: str, message: str, work: Callable[[], ResultT], on_success: Callable[[ResultT], None]) -> None:
        """Run `work` on a background thread behind a cancel-less `ProgressDialog`.

        `on_success` runs once `work` finishes, after the dialog is popped --
        never as the continuation of an awaited coroutine (a prior rendering
        bug traced list mutations that happened that way), always as a plain
        `on_worker_state_changed` event-handler callback instead.
        """
        self._progress_on_success = on_success
        dialog = ProgressDialog(title=title, message=message)
        self._progress_dialog = dialog
        self.app.push_screen(dialog)
        self.run_worker(
            work,
            thread=True,
            exclusive=True,
            exit_on_error=False,
            group=_PROGRESS_WORKER_GROUP,
            name=_PROGRESS_WORKER_GROUP,
        )

    def report_progress(self, completed: int, total: int) -> None:
        """Update the visible ProgressDialog's bar to a determinate completed/total display.

        Safe to call from the background thread running `run_with_progress`'s
        `work` callable -- hops back onto the app's event loop via
        `call_from_thread` rather than touching widgets directly off-thread.
        """
        dialog = self._progress_dialog
        if dialog is None:
            return
        self.app.call_from_thread(dialog.set_progress, completed, total)

    def report_stage_progress(self, message: str, completed: int, total: int) -> None:
        """Like `report_progress`, but also swaps the dialog's status message -- for multi-stage work.

        `total=0` means indeterminate for the stage in progress (see
        `ProgressDialog.set_progress`); a determinate `(completed, total)`
        only ever comes from a single stage, never a global count across
        stages, so the message is what tells the user which stage that is.
        """
        dialog = self._progress_dialog
        if dialog is None:
            return
        self.app.call_from_thread(dialog.update_message, message)
        self.app.call_from_thread(dialog.set_progress, completed, total)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group != _PROGRESS_WORKER_GROUP:
            return
        if event.state not in (WorkerState.SUCCESS, WorkerState.ERROR):
            return

        if isinstance(self.app.screen, ProgressDialog):
            self.app.pop_screen()
        self._progress_dialog = None

        on_success = self._progress_on_success
        self._progress_on_success = None

        if event.state == WorkerState.ERROR:
            self.notify(str(event.worker.error), severity="error")
            return

        if on_success is not None:
            on_success(event.worker.result)
