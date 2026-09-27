"""The processing coordinator: one run at a time, steps in order, and cancel, failure, restart, and progress handling.

Steps are scripted fakes over a fake application whose overview is computed from the steps that have completed, so
these tests exercise the coordinator itself rather than any real step.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import pytest
from tablesage_application.processing_steps import PROCESSING_STEPS, ProcessingOverview, StepID, StepState
from tablesage_tools.credentials import MissingCredential
from tablesage_tui.dialogs.generic import ConfirmationDialog
from tablesage_tui.dialogs.progress import ProgressDialog
from tablesage_tui.processing.coordinator import ProcessingCoordinator, Run, StepContext, StepFunction, StepResult
from tablesage_tui.screens.main_app import TableSageApp
from textual.pilot import Pilot
from textual.screen import ModalScreen


class _Processing:
    """A fake application's processing state: which steps are complete, and anything blocking."""

    def __init__(self, complete: set[StepID] | None = None) -> None:
        self.complete: set[StepID] = set(complete or ())
        self.blockers: tuple[str, ...] = ()
        self.application = MagicMock()
        self.application.processing_overview.side_effect = self.overview
        self.application.reopen_step.side_effect = lambda _sid, step_id: self.complete.discard(step_id)

    def overview(self, _session_id: uuid.UUID) -> ProcessingOverview:
        return ProcessingOverview(
            steps=tuple(StepState(step=step, complete=step.id in self.complete, visible=step.is_manual) for step in PROCESSING_STEPS),
            new_players=(),
            blockers=self.blockers,
        )


def _all_but(*step_ids: StepID) -> set[StepID]:
    return {step.id for step in PROCESSING_STEPS} - set(step_ids)


class _Steps(dict[StepID, StepFunction]):
    """A step function for every step; by default each succeeds and marks itself complete."""

    def __init__(self, processing: _Processing) -> None:
        super().__init__()
        self.processing = processing
        self.ran: list[StepID] = []
        for step in PROCESSING_STEPS:
            self[step.id] = self.completing(step.id)

    def completing(self, step_id: StepID, before: Callable[[StepContext], Any] | None = None) -> StepFunction:
        async def run(context: StepContext) -> StepResult:
            self.ran.append(step_id)
            if before is not None:
                result = before(context)
                if asyncio.iscoroutine(result):
                    await result
            self.processing.complete.add(step_id)
            return StepResult.success()

        return run

    def returning(self, step_id: StepID, result: StepResult) -> None:
        async def run(_context: StepContext) -> StepResult:
            self.ran.append(step_id)
            return result

        self[step_id] = run


def _app(processing: _Processing) -> tuple[TableSageApp, _Steps]:
    app = TableSageApp(processing.application)
    steps = _Steps(processing)
    app.coordinator = ProcessingCoordinator(app, steps)
    return app, steps


async def _wait_until_stopped(pilot: Pilot[Any], coordinator: ProcessingCoordinator) -> None:
    for _ in range(200):
        await pilot.pause(0.02)
        if not coordinator.is_running:
            await pilot.pause(0.05)
            return
    raise AssertionError("the run never stopped")


def test_every_step_needs_an_implementation() -> None:
    processing = _Processing()
    app = TableSageApp(processing.application)
    steps = _Steps(processing)
    del steps[StepID.ASSIGN_ROLES]

    with pytest.raises(RuntimeError, match="assign_roles"):
        ProcessingCoordinator(app, steps)


@pytest.mark.anyio
async def test_run_starts_at_the_first_incomplete_step_and_continues_to_the_end() -> None:
    processing = _Processing(_all_but(StepID.IDENTIFY_SPEAKERS, StepID.SUGGEST_GLOSSARY_TERMS, StepID.GENERATE_ARTIFACTS))
    app, steps = _app(processing)
    events: list[str] = []
    app.coordinator.subscribe(lambda _run, event: events.append(event))

    async with app.run_test() as pilot:
        assert app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)

    assert steps.ran == [StepID.IDENTIFY_SPEAKERS, StepID.SUGGEST_GLOSSARY_TERMS, StepID.GENERATE_ARTIFACTS]
    assert events[0] == "run_started" and events[-1] == "run_stopped"
    assert events.count("step_entered") == 3
    assert processing.application.clear_step_failure.call_count == 3


@pytest.mark.anyio
async def test_cancel_ends_the_run_without_running_later_steps() -> None:
    processing = _Processing(_all_but(StepID.REVIEW_GLOSSARY_TERMS, StepID.ADD_GLOSSARY_ENTRIES))
    app, steps = _app(processing)
    steps.returning(StepID.REVIEW_GLOSSARY_TERMS, StepResult.cancel())

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)

    assert steps.ran == [StepID.REVIEW_GLOSSARY_TERMS]
    processing.application.record_step_failure.assert_not_called()


@pytest.mark.anyio
async def test_error_is_recorded_on_the_step_with_the_run_id_and_ends_the_run() -> None:
    processing = _Processing(_all_but(StepID.IDENTIFY_SPEAKERS, StepID.SUGGEST_GLOSSARY_TERMS))
    app, steps = _app(processing)
    steps.returning(StepID.IDENTIFY_SPEAKERS, StepResult.error("Identify Speakers failed: no model"))
    run_ids: list[str] = []
    app.coordinator.subscribe(lambda run, _event: run_ids.append(run.run_id))
    session_id = uuid.uuid4()

    async with app.run_test() as pilot:
        app.coordinator.advance(session_id, trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)

    assert steps.ran == [StepID.IDENTIFY_SPEAKERS]
    processing.application.record_step_failure.assert_called_once_with(
        session_id, StepID.IDENTIFY_SPEAKERS, "Identify Speakers failed: no model", run_ids[0]
    )


@pytest.mark.anyio
async def test_an_exception_in_a_step_is_a_failure_named_after_the_step() -> None:
    processing = _Processing(_all_but(StepID.ASSIGN_ROLES))
    app, steps = _app(processing)

    async def explode(_context: StepContext) -> StepResult:
        raise RuntimeError("boom")

    steps[StepID.ASSIGN_ROLES] = explode

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)

    message = processing.application.record_step_failure.call_args.args[2]
    assert message == "Assign Roles To Players failed: boom"


@pytest.mark.anyio
async def test_a_second_advance_while_running_is_rejected() -> None:
    processing = _Processing(_all_but(StepID.REVIEW_TRANSCRIPT))
    app, steps = _app(processing)
    release = asyncio.Event()
    steps[StepID.REVIEW_TRANSCRIPT] = steps.completing(StepID.REVIEW_TRANSCRIPT, before=lambda _context: release.wait())

    async with app.run_test() as pilot:
        assert app.coordinator.advance(uuid.uuid4(), trigger="first")
        await pilot.pause(0.05)
        assert app.coordinator.is_running
        assert not app.coordinator.advance(uuid.uuid4(), trigger="second")
        release.set()
        await _wait_until_stopped(pilot, app.coordinator)

    assert steps.ran == [StepID.REVIEW_TRANSCRIPT]
    assert not app.coordinator.is_running


@pytest.mark.anyio
async def test_restart_reopens_the_step_then_runs_from_it() -> None:
    processing = _Processing(_all_but())
    app, steps = _app(processing)
    session_id = uuid.uuid4()

    async with app.run_test() as pilot:
        app.coordinator.advance(session_id, trigger="test", restart=StepID.REVIEW_SPELLING_CORRECTIONS)
        await _wait_until_stopped(pilot, app.coordinator)

    processing.application.reopen_step.assert_called_once_with(session_id, StepID.REVIEW_SPELLING_CORRECTIONS)
    assert steps.ran == [StepID.REVIEW_SPELLING_CORRECTIONS]


@pytest.mark.anyio
async def test_blocked_session_runs_nothing() -> None:
    processing = _Processing()
    processing.blockers = ("This Session has no attendees. Add them on Session Detail.",)
    app, steps = _app(processing)

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)

    assert steps.ran == []


@pytest.mark.anyio
async def test_a_step_that_never_completes_its_outputs_is_not_repeated_forever() -> None:
    processing = _Processing(_all_but(StepID.APPLY_NAME_CORRECTIONS))
    app, steps = _app(processing)
    steps.returning(StepID.APPLY_NAME_CORRECTIONS, StepResult.success())

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)

    assert steps.ran == [StepID.APPLY_NAME_CORRECTIONS, StepID.APPLY_NAME_CORRECTIONS]
    assert processing.application.record_step_failure.call_args.args[2] == "Apply Name Corrections finished without producing its output."


@pytest.mark.anyio
async def test_progress_dialog_is_shared_by_automatic_steps_and_closed_when_the_run_ends() -> None:
    processing = _Processing(_all_but(StepID.IDENTIFY_SPEAKERS, StepID.SUGGEST_GLOSSARY_TERMS))
    app, steps = _app(processing)
    seen: list[list[str]] = []

    async def background(context: StepContext) -> None:
        await context.background("working…", lambda: None)
        seen.append([type(screen).__name__ for screen in app.screen_stack])

    for step_id in (StepID.IDENTIFY_SPEAKERS, StepID.SUGGEST_GLOSSARY_TERMS):
        steps[step_id] = steps.completing(step_id, before=background)

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)
        stack = [type(screen).__name__ for screen in app.screen_stack]

    assert [names.count("ProgressDialog") for names in seen] == [1, 1]
    assert "ProgressDialog" not in stack


@pytest.mark.anyio
async def test_progress_dialog_is_closed_when_a_step_fails() -> None:
    processing = _Processing(_all_but(StepID.IDENTIFY_SPEAKERS))
    app, steps = _app(processing)

    async def fail(context: StepContext) -> StepResult:
        await context.background("working…", lambda: None)
        raise RuntimeError("boom")

    steps[StepID.IDENTIFY_SPEAKERS] = fail

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)
        assert not any(isinstance(screen, ProgressDialog) for screen in app.screen_stack)


class _Answer(ModalScreen[str]):
    def on_mount(self) -> None:
        self.set_timer(0.05, self._answer)

    def _answer(self) -> None:
        self.dismiss("answer")


@pytest.mark.anyio
async def test_showing_a_screen_closes_the_progress_dialog_and_returns_its_result() -> None:
    processing = _Processing(_all_but(StepID.REVIEW_TRANSCRIPT))
    app, steps = _app(processing)
    results: list[object] = []

    async def show(context: StepContext) -> None:
        await context.background("preparing…", lambda: None)
        results.append(await context.show(_Answer()))
        results.append(any(isinstance(screen, ProgressDialog) for screen in app.screen_stack))

    steps[StepID.REVIEW_TRANSCRIPT] = steps.completing(StepID.REVIEW_TRANSCRIPT, before=show)

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)

    assert results == ["answer", False]


@pytest.mark.anyio
async def test_missing_credential_for_an_automatic_step_fails_it_and_offers_settings() -> None:
    processing = _Processing(_all_but(StepID.SUGGEST_GLOSSARY_TERMS))
    processing.application.require_credentials.side_effect = MissingCredential("openai", "openai/gpt")
    app, steps = _app(processing)

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)
        assert isinstance(app.screen, ConfirmationDialog)

    assert steps.ran == []
    processing.application.record_step_failure.assert_called_once()


@pytest.mark.anyio
async def test_progress_reported_from_a_worker_thread_reaches_listeners() -> None:
    processing = _Processing(_all_but(StepID.IDENTIFY_SPEAKERS))
    app, steps = _app(processing)
    messages: list[str | None] = []

    def on_event(run: Run, event: str) -> None:
        if event == "progress":
            messages.append(run.progress_message)

    async def work(context: StepContext) -> None:
        await context.background("starting…", lambda: context.progress("halfway", 1, 2))

    steps[StepID.IDENTIFY_SPEAKERS] = steps.completing(StepID.IDENTIFY_SPEAKERS, before=work)
    app.coordinator.subscribe(on_event)

    async with app.run_test() as pilot:
        app.coordinator.advance(uuid.uuid4(), trigger="test")
        await _wait_until_stopped(pilot, app.coordinator)

    assert messages[:2] == ["starting…", "halfway"]
