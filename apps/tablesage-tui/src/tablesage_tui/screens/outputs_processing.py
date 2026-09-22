from __future__ import annotations

import uuid

from tablesage_application.session_pipeline.artifact_graph import (
    GENERATION_LABELS,
    GENERATION_ORDER,
    ArtifactStatus,
    GenerationTask,
)
from tablesage_model.model import SessionProcessingPhase
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Static

from ..generation_runner import GenerationRunner
from .session_processing import SessionProcessingScreen, register_processing_screen


class OutputsProcessingScreen(SessionProcessingScreen):
    """Summarize, generate, and safely retry a Session's output artifacts."""

    section = "process · outputs"
    phase = SessionProcessingPhase.OUTPUTS
    AUTO_FOCUS = "#outputs-generate-button"
    COMMON_BINDINGS = [
        *SessionProcessingScreen.COMMON_BINDINGS,
        Binding("g,G", "generate_outputs", "Generate", key_display="G"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__(session_id)
        self._plan: tuple[GenerationTask, ...] = ()
        self._planning_error = ""
        self._runner = GenerationRunner(
            self,
            session_id,
            on_start=self._generation_started,
            on_success=self._generation_succeeded,
            on_error=self._generation_failed,
        )

    def compose_content(self) -> ComposeResult:
        with Vertical(id="outputs-processing-panel", classes="panel surface-2") as panel:
            panel.border_title = " outputs "
            yield Static("", id="outputs-processing-summary")
            yield Static("", id="outputs-processing-error", classes="processing-error")
            with Vertical(id="outputs-status-list"):
                for artifact in GENERATION_ORDER:
                    yield Static("", id=f"output-status-{artifact.value}", classes="output-status")
            yield Button("Generate Outputs", id="outputs-generate-button", variant="primary")

    def on_mount(self) -> None:
        super().on_mount()
        button = self.query_one("#outputs-generate-button", Button)
        if not button.disabled:
            button.focus()

    def refresh_data(self) -> None:
        super().refresh_data()
        artifact_states = self.application.session_artifact_states(self.session_id)
        for artifact in GENERATION_ORDER:
            status = artifact_states[artifact]
            symbol = {
                ArtifactStatus.CURRENT: "●",
                ArtifactStatus.STALE: "◐",
                ArtifactStatus.MISSING: "○",
            }.get(status, "○")
            self.query_one(f"#output-status-{artifact.value}", Static).update(f"{symbol} {GENERATION_LABELS[artifact]}")

        self._planning_error = ""
        try:
            self._plan = self.application.generation_plan(self.session_id)
        except Exception as exc:
            self._plan = ()
            self._planning_error = str(exc)

        state = self.application.session_processing_state(self.session_id)
        finalization_pending = self.application.bootstrap_finalization_pending(self.session_id) is True
        persisted_error = ""
        if state is not None and state.failed_phase == self.phase.value:
            persisted_error = state.failure_message or ""
        error = persisted_error or self._planning_error
        self.query_one("#outputs-processing-error", Static).update(error)

        button = self.query_one("#outputs-generate-button", Button)
        if error:
            button.label = "Retry Generation"
        else:
            button.label = "Generate Outputs"
        button.disabled = not self._plan and not error and not finalization_pending

        summary = self.query_one("#outputs-processing-summary", Static)
        if not self._plan and not error:
            summary.update("Outputs are current; finalize bootstrap profiles." if finalization_pending else "All outputs are current.")
        elif self._plan:
            prior_count = len({task.session_id for task in self._plan if task.session_id != self.session_id})
            prior_note = f" across {prior_count} prior Session{'s' if prior_count != 1 else ''}" if prior_count else ""
            summary.update(f"{len(self._plan)} generation step{'s' if len(self._plan) != 1 else ''} needed{prior_note}.")
        else:
            summary.update("Generation needs attention before it can continue.")
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "generate_outputs":
            state = self.application.session_processing_state(self.session_id)
            has_error = state is not None and state.failed_phase == self.phase.value
            finalization_pending = self.application.bootstrap_finalization_pending(self.session_id) is True
            return True if self._plan or has_error or self._planning_error or finalization_pending else None
        return super().check_action(action, parameters)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "outputs-generate-button":
            self.action_generate_outputs()

    def action_generate_outputs(self) -> None:
        self._runner.prepare()

    def _generation_started(self) -> None:
        self.application.clear_session_processing_failure(self.session_id)
        self.refresh_data()

    def _generation_succeeded(self, result: tuple[GenerationTask, ...]) -> None:
        self.processing_succeeded(SessionProcessingPhase.OUTPUTS)
        self.refresh_data()
        self.notify("Outputs generated." if result else "All outputs are current.")

    def _generation_failed(self, error: BaseException) -> None:
        message = str(error)
        self.processing_failed(message)
        self.refresh_data()
        self.notify(message, severity="error")


register_processing_screen(SessionProcessingPhase.OUTPUTS, OutputsProcessingScreen)
