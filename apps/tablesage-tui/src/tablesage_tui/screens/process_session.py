from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from rich.text import Text
from tablesage_application.processing_steps import (
    ProcessingOverview,
    ProcessingStep,
    StepID,
    StepState,
    next_manual_step,
)
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static
from textual.worker import Worker, WorkerState

from .base import TableSageScreen

if TYPE_CHECKING:
    from ..processing.coordinator import ProcessingCoordinator, Run
    from .main_app import TableSageApp

_OVERVIEW_WORKER_GROUP = "process-session-overview"
# Draw automatic steps too, each with its own completion indicator. False shows only the manual steps, with an
# automatic step's progress and failures on the row of the manual step it leads to.
SHOW_AUTOMATIC_STEPS = True
_DIM = "dim"


class _ProcessingStepsTable(DataTable[object]):
    """A processing table whose arrow keys visit review points, not every automatic operation."""

    def __init__(self, *, is_manual: Callable[[int], bool]) -> None:
        super().__init__(id="process-session-steps", cursor_type="row", zebra_stripes=False, classes="tablesage-table")
        self._is_manual = is_manual

    def action_cursor_up(self) -> None:
        self._move_to_manual(-1)

    def action_cursor_down(self) -> None:
        self._move_to_manual(1)

    def _move_to_manual(self, direction: int) -> None:
        if not (self.show_cursor and self.cursor_type == "row"):
            if direction < 0:
                super().action_scroll_up()
            else:
                super().action_scroll_down()
            return

        candidate = self.cursor_coordinate.row + direction
        while 0 <= candidate < self.row_count and not self._is_manual(candidate):
            candidate += direction
        if 0 <= candidate < self.row_count:
            self.move_cursor(row=candidate)


class ProcessSessionScreen(TableSageScreen):
    """Where a Session is processed: its manual steps, a Continue button, and restarting from an earlier step.

    Only manual steps are shown -- the ones that ask something of you -- and only those that apply to this
    Session. Automatic steps report on the row of the manual step they lead to: what is running, or why it failed.
    Continue runs processing from the first incomplete step; selecting a completed row (Enter or R) restarts from
    it. This screen never starts processing on its own: it shows the coordinator's runs and asks it to advance.
    """

    section = "process session"
    HIDDEN_BINDINGS = [Binding("escape", "pop_screen", "Back", show=False)]
    COMMON_BINDINGS = [
        Binding("c,C", "continue_processing", "Continue", key_display="C"),
        Binding("enter,r,R", "restart_step", "Restart Step", key_display="R"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__()
        self._session_id = session_id
        self._overview: ProcessingOverview | None = None
        self._rows: list[StepState] = []

    @property
    def session_id(self) -> uuid.UUID:
        return self._session_id

    @property
    def _coordinator(self) -> ProcessingCoordinator:
        return cast("TableSageApp", self.app).coordinator

    def compose_content(self) -> ComposeResult:
        with Vertical(id="process-session-panel", classes="panel surface-2") as panel:
            panel.border_title = " Process Session "
            with Horizontal(id="process-session-columns"):
                with Vertical(id="process-session-steps-column"):
                    yield Static("Session Processing Steps", id="process-session-steps-header", classes="section-title")
                    table = _ProcessingStepsTable(is_manual=lambda row: row < len(self._rows) and self._rows[row].step.is_manual)
                    table.add_column("", key="status", width=2)
                    table.add_column("Step", key="step")
                    table.add_column("", key="note")
                    yield table
                with Vertical(id="process-session-side-column"):
                    yield Static("New Players", id="process-session-new-players-header", classes="section-title")
                    yield Static("", id="process-session-new-player-list", markup=False)
            with Horizontal(id="process-session-actions"):
                yield Button("Continue", id="process-session-continue", variant="primary", disabled=True)

    def on_mount(self) -> None:
        self._coordinator.subscribe(self._on_run_event)
        self._refresh_overview()
        self.query_one("#process-session-steps", DataTable).focus()

    def on_unmount(self) -> None:
        self._coordinator.unsubscribe(self._on_run_event)

    def on_screen_resume(self) -> None:
        # Coming back to this screen only refreshes what it shows; it never starts processing.
        self._refresh_overview()

    def refresh_data(self) -> None:
        self._refresh_overview()

    # Overview

    def _refresh_overview(self) -> None:
        self.run_worker(
            lambda: self.application.processing_overview(self._session_id),
            thread=True,
            exclusive=True,
            group=_OVERVIEW_WORKER_GROUP,
            exit_on_error=False,
        )

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.worker.group != _OVERVIEW_WORKER_GROUP:
            super().on_worker_state_changed(event)
            return
        if event.state is WorkerState.SUCCESS:
            self._show(cast("ProcessingOverview", event.worker.result))
        elif event.state is WorkerState.ERROR:
            self.notify(f"Could not read this Session's processing state: {event.worker.error}", severity="error")

    def _on_run_event(self, run: Run, event: str) -> None:
        if run.session_id != self._session_id:
            return
        # A step starting or the run stopping changes what's complete; progress only changes a row's note.
        if event in ("run_stopped", "step_entered"):
            self._refresh_overview()
        elif self._overview is not None:
            self._show(self._overview)

    def _active_run(self) -> Run | None:
        run = self._coordinator.current_run
        return run if run is not None and run.session_id == self._session_id else None

    @staticmethod
    def _drawn(state: StepState) -> bool:
        return state.visible and (SHOW_AUTOMATIC_STEPS or state.step.is_manual)

    @staticmethod
    def _row_for(step: ProcessingStep) -> ProcessingStep | None:
        """The row that shows `step`: itself when drawn, else the manual step it leads to."""
        return step if SHOW_AUTOMATIC_STEPS or step.is_manual else next_manual_step(step.id)

    def _current_row_step(self, overview: ProcessingOverview) -> ProcessingStep | None:
        step = overview.next_step
        return None if step is None else self._row_for(step)

    def _show(self, overview: ProcessingOverview) -> None:
        self._overview = overview
        run = self._active_run()
        current_row = self._current_row_step(overview)
        running_row = (None if run.step is None else self._row_for(run.step)) if run else None

        # Failures show on the step's own row, or, for a hidden automatic step, the row it leads to.
        failures: dict[StepID, str] = {}
        for state in overview.steps:
            if state.failure is not None:
                row = self._row_for(state.step)
                if row is not None:
                    failures.setdefault(row.id, state.failure)

        self._rows = [state for state in overview.steps if self._drawn(state)]
        table = self.query_one("#process-session-steps", DataTable)
        selected = table.cursor_row
        table.clear()
        future = False
        for state in self._rows:
            step = state.step
            is_current = current_row is not None and step.id is current_row.id
            is_running = running_row is not None and step.id is running_row.id and run is not None and run.step is not None
            has_failure = step.id in failures
            if is_running:
                status, note = Text("▶", style="bold"), Text(self._running_note(run), style="italic")
            elif has_failure:
                status, note = Text("!", style="bold red"), Text(failures[step.id], style="red")
            elif state.complete:
                status_style = "bold green" if step.is_manual else "dim green"
                status, note = Text("✓", style=status_style), Text("Nothing to review" if state.nothing_to_review else "", style=_DIM)
            elif is_current:
                status, note = Text("›", style="bold"), Text("")
            else:
                status, note = Text(""), Text("")
            # Rows after the current one can't start yet. Automatic steps are indented and muted under the manual steps they serve.
            label = step.label if step.is_manual else f"  {step.label}"
            label_style = "bold" if step.is_manual else ("" if is_running or has_failure else _DIM)
            if future:
                label_style = _DIM
            table.add_row(status, Text(label, style=label_style), note, key=step.id.value)
            future = future or is_current
        if self._rows:
            table.move_cursor(row=min(max(selected, 0), len(self._rows) - 1))

        players = "\n".join(f"• {name}" for name in overview.new_players)
        self.query_one("#process-session-new-player-list", Static).update(players)
        self.query_one("#process-session-side-column").display = bool(overview.new_players)
        self._update_continue(overview, run)
        self.refresh_bindings()

    @staticmethod
    def _running_note(run: Run) -> str:
        assert run.step is not None
        if run.step.is_manual:
            return "In progress"
        return f"preparing: {run.progress_message or run.step.label + '…'}"

    def _update_continue(self, overview: ProcessingOverview, run: Run | None) -> None:
        button = self.query_one("#process-session-continue", Button)
        if run is not None or self._coordinator.is_running:
            button.label, button.disabled = "Processing…", True
        elif overview.blockers:
            button.label, button.disabled = overview.blockers[0], True
        elif overview.next_step is None:
            button.label, button.disabled = "All steps complete", True
        else:
            button.label, button.disabled = f"Continue: {overview.next_step.label}", False
        # A laid-out Button keeps its old auto width when only its label changes; re-applying the width re-measures it.
        button.styles.width = None
        button.styles.width = "auto"

    # Actions

    def _selected(self) -> StepState | None:
        table = self.query_one("#process-session-steps", DataTable)
        if not self._rows or not 0 <= table.cursor_row < len(self._rows):
            return None
        return self._rows[table.cursor_row]

    def _can_restart(self, state: StepState) -> bool:
        """Completed rows can be restarted; the current row just continues. Rows after it can't start yet."""
        assert self._overview is not None
        current_row = self._current_row_step(self._overview)
        return state.complete or (current_row is not None and state.step.id is current_row.id)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        idle = not self._coordinator.is_running and self._overview is not None and not self._overview.blockers
        if action == "continue_processing":
            return True if idle and self._overview is not None and self._overview.next_step is not None else None
        if action == "restart_step":
            state = self._selected()
            return True if idle and state is not None and self._can_restart(state) else None
        return super().check_action(action, parameters)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "process-session-continue":
            self.action_continue_processing()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        if self.check_action("restart_step", ()):
            self.action_restart_step()

    def action_continue_processing(self) -> None:
        if self.check_action("continue_processing", ()):
            self._coordinator.advance(self._session_id, trigger="continue_button")

    def action_restart_step(self) -> None:
        state = self._selected()
        if state is None or not self.check_action("restart_step", ()):
            return
        if state.complete:
            self._coordinator.advance(self._session_id, trigger=f"restart:{state.step.id.value}", restart=state.step.id)
        else:
            self._coordinator.advance(self._session_id, trigger="continue_row")
