"""The processing coordinator: the only thing that starts Session processing work.

One coordinator lives on the app. `advance` starts a run -- one async worker that runs steps in order from the
first incomplete step, opening each manual step's screen and continuing after it, until a step is cancelled or
fails or everything is complete. A second `advance` while a run is active is rejected and logged, so two runs can
never overlap. Screens never drive processing: they show a run's progress and ask the coordinator to advance.

Each step is a linear async function (see `steps`) that uses a `StepContext`. Consecutive automatic steps share
one progress dialog, which the run closes before any manual step's screen opens and, whatever happens, when the
run ends -- a dialog can't outlive the code that opened it.

Every log line of a run carries its `run_id` and `trigger`: `processing.run_started`, `processing.step_entered`,
`processing.step_outcome`, `processing.run_stopped`, and `processing.advance_rejected`; `processing.run` is the
whole run's wide event. A failed step's message is also kept in the Session's processing state for its row.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, TypeVar

import widelog
from tablesage_application.processing_steps import ProcessingOverview, ProcessingStep, StepID
from tablesage_tools.credentials import MissingCredential
from textual.notifications import SeverityLevel
from textual.screen import Screen

from ..dialogs.generic import ConfirmationDialog
from ..dialogs.progress import ProgressDialog

if TYPE_CHECKING:
    from tablesage_application import Application

    from ..screens.main_app import TableSageApp

_ResultT = TypeVar("_ResultT")
_RUN_WORKER_GROUP = "processing-run"
# A step that reports success yet leaves its outputs incomplete this many times in a row stops the run.
_MAX_REPEATS = 2


class Outcome(StrEnum):
    SUCCESS = "success"
    CANCEL = "cancel"
    ERROR = "error"


@dataclass(frozen=True)
class StepResult:
    outcome: Outcome
    message: str | None = None

    @classmethod
    def success(cls, message: str | None = None) -> StepResult:
        return cls(Outcome.SUCCESS, message)

    @classmethod
    def cancel(cls) -> StepResult:
        return cls(Outcome.CANCEL)

    @classmethod
    def error(cls, message: str) -> StepResult:
        return cls(Outcome.ERROR, message)


class StopReason(StrEnum):
    ALL_COMPLETE = "all_complete"
    CANCELLED = "cancelled"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Run:
    session_id: uuid.UUID
    run_id: str
    trigger: str
    # Values a trigger passes to its steps, such as the artifact Regenerate Artifact forces.
    facts: dict[str, Any] = field(default_factory=dict)
    step: ProcessingStep | None = None
    progress_message: str | None = None


RunListener = Callable[[Run, str], None]


class StepContext:
    """What a step function can do: run blocking work behind the shared progress dialog, show a screen and wait for
    its result, report progress, and read the run's facts."""

    def __init__(self, coordinator: ProcessingCoordinator, run: Run) -> None:
        self._coordinator = coordinator
        self.run = run

    @property
    def app(self) -> TableSageApp:
        return self._coordinator.app

    @property
    def application(self) -> Application:
        return self._coordinator.app.application

    @property
    def session_id(self) -> uuid.UUID:
        return self.run.session_id

    @property
    def facts(self) -> dict[str, Any]:
        return self.run.facts

    async def background(self, message: str, work: Callable[[], _ResultT]) -> _ResultT:
        """Run `work` on a thread behind the run's progress dialog (opened if needed), titled with the current step."""
        await self._coordinator.show_progress(message)
        return await asyncio.to_thread(work)

    async def call(self, work: Callable[[], _ResultT]) -> _ResultT:
        """Run quick blocking work (a small read or write) off the UI thread, without a progress dialog."""
        return await asyncio.to_thread(work)

    def progress(self, message: str, completed: int = 0, total: int = 0) -> None:
        """Update the progress dialog from the step's worker thread; `total=0` is indeterminate."""
        self._coordinator.report_progress(message, completed, total)

    async def show(self, screen: Screen[_ResultT]) -> _ResultT | None:
        """Close the progress dialog, show `screen`, and return what it dismisses with (None means cancel)."""
        await self._coordinator.close_progress()
        return await self.app.push_screen_wait(screen)

    async def confirm(self, **dialog: Any) -> bool | None:
        return await self.show(ConfirmationDialog(**dialog))

    def notify(self, message: str, *, severity: SeverityLevel = "information") -> None:
        self.app.notify(message, severity=severity)


StepFunction = Callable[[StepContext], Awaitable[StepResult]]


class ProcessingCoordinator:
    def __init__(self, app: TableSageApp, steps: dict[StepID, StepFunction]) -> None:
        missing = [step_id.value for step_id in StepID if step_id not in steps]
        if missing:
            raise RuntimeError(f"Processing steps without an implementation: {', '.join(missing)}")
        self.app = app
        self._steps = steps
        self._run: Run | None = None
        self._listeners: list[RunListener] = []
        self._progress: ProgressDialog | None = None

    # State and listeners

    @property
    def current_run(self) -> Run | None:
        return self._run

    @property
    def is_running(self) -> bool:
        return self._run is not None

    def subscribe(self, listener: RunListener) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: RunListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _emit(self, run: Run, event: str) -> None:
        for listener in list(self._listeners):
            listener(run, event)

    def _log(self, run: Run | None, op: str, **fields: object) -> None:
        run_fields: dict[str, object] = (
            {"run_id": run.run_id, "trigger": run.trigger, "session_id": str(run.session_id)} if run is not None else {}
        )
        with widelog.wide_event(op=f"processing.{op}", **run_fields, **fields):
            pass

    # Starting a run

    def advance(self, session_id: uuid.UUID, *, trigger: str, restart: StepID | None = None, facts: dict[str, Any] | None = None) -> bool:
        """Start a run for `session_id` from its first incomplete step -- after reopening `restart`, if given.
        Returns False, and logs why, when a run is already active."""
        if self._run is not None:
            self._log(
                self._run,
                "advance_rejected",
                requested_session_id=str(session_id),
                requested_trigger=trigger,
                active_step=self._run.step.id.value if self._run.step is not None else None,
            )
            self.app.notify("Processing is already running.", severity="warning")
            return False
        run = Run(session_id=session_id, run_id=uuid.uuid4().hex[:12], trigger=trigger, facts=dict(facts or {}))
        self._run = run
        self._log(run, "run_started", restart=restart.value if restart is not None else None)
        self._emit(run, "run_started")
        self.app.run_worker(self._run_steps(run, restart), group=_RUN_WORKER_GROUP, name=f"processing-{run.run_id}", exit_on_error=False)
        return True

    async def _run_steps(self, run: Run, restart: StepID | None) -> None:
        durations: dict[str, float] = {}
        outcomes: dict[str, str] = {}
        reason = StopReason.ALL_COMPLETE
        stopped_step: str | None = None
        with widelog.wide_event(op="processing.run", run_id=run.run_id, trigger=run.trigger, session_id=str(run.session_id)) as log:
            try:
                application = self.app.application
                if restart is not None:
                    await asyncio.to_thread(application.reopen_step, run.session_id, restart)
                previous: StepID | None = None
                repeats = 0
                while True:
                    overview: ProcessingOverview = await asyncio.to_thread(application.processing_overview, run.session_id)
                    if overview.blockers:
                        reason, stopped_step = StopReason.BLOCKED, None
                        self.app.notify(overview.blockers[0], severity="error")
                        break
                    step = overview.next_step
                    if step is None:
                        break
                    repeats = repeats + 1 if step.id is previous else 0
                    if repeats >= _MAX_REPEATS:
                        message = f"{step.label} finished without producing its output."
                        await self._fail(run, step, message)
                        reason, stopped_step = StopReason.FAILED, step.id.value
                        break
                    previous = step.id

                    run.step = step
                    run.progress_message = None
                    self._log(run, "step_entered", step=step.id.value, kind=step.kind.value)
                    self._emit(run, "step_entered")
                    started = time.monotonic()
                    result = await self._run_step(run, step)
                    durations[step.id.value] = round(time.monotonic() - started, 1)
                    outcomes[step.id.value] = result.outcome.value
                    self._log(run, "step_outcome", step=step.id.value, outcome=result.outcome.value, message=result.message)

                    if result.outcome is Outcome.CANCEL:
                        reason, stopped_step = StopReason.CANCELLED, step.id.value
                        break
                    if result.outcome is Outcome.ERROR:
                        await self._fail(run, step, result.message or f"{step.label} failed.")
                        reason, stopped_step = StopReason.FAILED, step.id.value
                        break
                    await asyncio.to_thread(application.clear_step_failure, run.session_id, step.id)
                    if result.message:
                        self.app.notify(result.message)
            except Exception as exc:  # noqa: BLE001 - reading processing state failed; stop and say so
                reason, stopped_step = StopReason.FAILED, run.step.id.value if run.step is not None else None
                log.set(error=f"{type(exc).__name__}: {exc}")
                self.app.notify(f"Processing stopped: {exc}", severity="error")
            finally:
                await self.close_progress()
                log.set(step_durations_s=durations, step_outcomes=outcomes, stop_reason=reason.value, stopped_step=stopped_step)
                self._log(run, "run_stopped", reason=reason.value, step=stopped_step)
                self._run = None
                self._emit(run, "run_stopped")

    async def _run_step(self, run: Run, step: ProcessingStep) -> StepResult:
        context = StepContext(self, run)
        try:
            if not step.is_manual:
                self.app.application.require_credentials(*step.llm_roles, transcription=step.needs_transcription)
            return await self._steps[step.id](context)
        except MissingCredential as exc:
            await self.close_progress()
            self._show_missing_credential(exc)
            return StepResult.error(str(exc))
        except Exception as exc:  # noqa: BLE001 - any step failure stops the run and is shown on its row
            with widelog.wide_event(op="processing.step_exception", run_id=run.run_id, step=step.id.value) as log:
                log.set(error=f"{type(exc).__name__}: {exc}")
            cause: BaseException | None = exc
            while cause is not None and not isinstance(cause, MissingCredential):
                cause = cause.__cause__
            if isinstance(cause, MissingCredential):
                await self.close_progress()
                self._show_missing_credential(cause)
            return StepResult.error(f"{step.label} failed: {exc}")

    async def _fail(self, run: Run, step: ProcessingStep, message: str) -> None:
        await self.close_progress()
        await asyncio.to_thread(self.app.application.record_step_failure, run.session_id, step.id, message, run.run_id)
        self.app.notify(message, severity="error")

    def _show_missing_credential(self, error: MissingCredential) -> None:
        def on_answer(answer: bool | None) -> None:
            if answer:
                self.app.action_open_settings()

        self.app.push_screen(
            ConfirmationDialog(
                title="Provider key required", prompt=str(error), show_cancel=False, no_label="Cancel", yes_label="Open Settings"
            ),
            on_answer,
        )

    # The shared progress dialog

    async def show_progress(self, message: str) -> None:
        run = self._run
        title = run.step.label if run is not None and run.step is not None else "Processing"
        if self._progress is None or not self._progress.is_attached:
            self._progress = ProgressDialog(title=title, message=message)
            await self.app.push_screen(self._progress)
        else:
            self._progress.update_title(title)
            self._progress.update_message(message)
            self._progress.set_progress(0, 0)
        if run is not None:
            run.progress_message = message
            self._emit(run, "progress")

    def report_progress(self, message: str, completed: int, total: int) -> None:
        """Thread-safe: called from a step's worker thread."""
        dialog = self._progress
        if dialog is None:
            return

        run = self._run

        def update() -> None:
            if dialog.is_attached:
                dialog.update_message(message)
                dialog.set_progress(completed, total)
            if run is not None and run.progress_message != message:
                run.progress_message = message
                self._emit(run, "progress")

        self.app.call_from_thread(update)

    async def close_progress(self) -> None:
        dialog, self._progress = self._progress, None
        if dialog is None or not dialog.is_attached:
            return
        if self.app.screen is dialog:
            await self.app.pop_screen()
            return
        # Steps close the dialog before showing anything else, so this is never expected; log it rather than
        # leave a dialog behind or fail the run.
        with widelog.wide_event(op="processing.progress_dialog_not_on_top", screen_stack=[type(s).__name__ for s in self.app.screen_stack]):
            pass
