from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, cast

from tablesage_application import Application
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer
from textual.worker import Worker, WorkerState

from ..dialogs.generic import ConfirmationDialog
from ..dialogs.other_actions import OtherActionsDialog
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

    # Every full-page screen inherits this hidden refresh binding.
    BINDINGS = [
        Binding("f5", "refresh_screen", "Refresh", key_display="F5", show=False),
    ]
    COMMON_BINDINGS: ClassVar[list[Binding]] = []
    OTHER_BINDINGS: ClassVar[list[Binding]] = []
    HIDDEN_BINDINGS: ClassVar[list[Binding]] = []

    def __init__(self, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        # Install the grouped declarations on this screen's map so both dispatch
        # and the Footer use the same source lists.
        for binding in self.HIDDEN_BINDINGS:
            self._bindings.bind(
                binding.key,
                binding.action,
                binding.description,
                show=False,
                key_display=binding.key_display,
                priority=binding.priority,
            )
        for binding in self.COMMON_BINDINGS:
            self._bindings.bind(
                binding.key,
                binding.action,
                binding.description,
                show=binding.show,
                key_display=binding.key_display,
                priority=binding.priority,
            )
        for binding in self.OTHER_BINDINGS:
            self._bindings.bind(
                binding.key,
                binding.action,
                binding.description,
                show=False,
                key_display=binding.key_display,
                priority=binding.priority,
            )
        if self.OTHER_BINDINGS:
            self._bindings.bind("question_mark,slash", "show_other_actions", "Other actions", key_display="?")

    _progress_on_success: Callable[[Any], None] | None = None
    _progress_on_error: Callable[[BaseException], None] | None = None
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

    def action_show_other_actions(self) -> None:
        """Open the secondary-action menu, then run the selected action on this screen."""
        if not self.OTHER_BINDINGS:
            return

        def run_selected(action: str | None) -> None:
            if action is not None:
                self.call_later(self.app.run_action, action, default_namespace=self)

        self.app.push_screen(OtherActionsDialog(self.OTHER_BINDINGS), run_selected)

    def refresh_data(self) -> None:
        """Reload the data this screen displays. No-op by default; override in screens that show live data."""

    def run_with_folder_collision_check(
        self,
        *,
        title: str,
        prompt: str,
        exists: Callable[[], bool],
        delete_existing: Callable[[], None],
        proceed: Callable[[], None],
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        """Guard a create/rename that's about to claim an on-disk folder against a stray orphan already sitting there.

        `exists`/`delete_existing`/`proceed` are the three ends the caller
        wires up (an existence check, a deletion, and the actual create/rename);
        this owns the shared middle -- no collision runs `proceed` straight
        away, a collision prompts "delete and continue?" and only calls
        `delete_existing` then `proceed` on confirmation. Cancelling always
        aborts outright (consistent with every other confirmation dialog in
        the app) rather than looping back to retry -- `on_cancel`, if given, is
        for cosmetic cleanup only (e.g. resetting an input field), not a retry.
        """
        if not exists():
            proceed()
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                delete_existing()
                proceed()
            elif on_cancel is not None:
                on_cancel()

        self.app.push_screen(ConfirmationDialog(title=title, prompt=prompt), on_confirm)

    def run_with_progress(
        self,
        *,
        title: str,
        message: str,
        work: Callable[[], ResultT],
        on_success: Callable[[ResultT], None],
        on_error: Callable[[BaseException], None] | None = None,
    ) -> None:
        """Run `work` on a background thread behind a cancel-less `ProgressDialog`.

        `on_success` runs once `work` finishes, after the dialog is popped --
        never as the continuation of an awaited coroutine (a prior rendering
        bug traced list mutations that happened that way), always as a plain
        `on_worker_state_changed` event-handler callback instead. That callback
        is itself deferred via `call_after_refresh` (see `on_worker_state_changed`)
        so any widget mutation it makes (e.g. reloading a list) lands after the
        dialog-pop's own screen transition has rendered, not racing it.

        `on_error`, if given, replaces the default error toast on failure -- for callers that
        want to route the failure somewhere more durable (e.g. a permanent error table) instead
        of (or in addition to) a toast. Every other caller keeps today's plain toast.
        """
        self._progress_on_success = on_success
        self._progress_on_error = on_error
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
        on_error = self._progress_on_error
        self._progress_on_error = None

        if event.state == WorkerState.ERROR:
            assert event.worker.error is not None
            if on_error is not None:
                on_error(event.worker.error)
            else:
                self.notify(str(event.worker.error), severity="error")
            return

        if on_success is not None:
            # Deferred, not called inline: popping the ProgressDialog above schedules its own
            # screen-transition render; calling straight into `on_success` here can mutate the
            # revealed screen's widgets (e.g. reloading a table) before that transition has
            # rendered, so the mutation loses the race and the screen shows stale content until
            # something else (e.g. F5) forces a further repaint. `call_after_refresh` runs the
            # callback only once the pop's own refresh has gone out.
            self.call_after_refresh(on_success, event.worker.result)
