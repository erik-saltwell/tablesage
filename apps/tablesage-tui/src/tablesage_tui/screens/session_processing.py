from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import ClassVar

from tablesage_application.paths import ArtifactName
from tablesage_application.session_pipeline.artifact_graph import GENERATION_ORDER, ArtifactStatus
from tablesage_model.model import SessionProcessingPhase
from textual.app import ComposeResult
from textual.binding import Binding

from ..widgets.workflow_rail import WorkflowRail, WorkflowStepStatus
from .base import TableSageScreen

ProcessingScreenFactory = Callable[[uuid.UUID], "SessionProcessingScreen"]

_PROCESSING_SCREEN_FACTORIES: dict[SessionProcessingPhase, ProcessingScreenFactory] = {}


def register_processing_screen(phase: SessionProcessingPhase, factory: ProcessingScreenFactory) -> None:
    """Register the screen factory used to replace the active Process-flow stage."""
    _PROCESSING_SCREEN_FACTORIES[phase] = factory


class SessionProcessingScreen(TableSageScreen):
    """Shared shell and navigation for one stage of the Session Process flow.

    Concrete Audio, Transcript, and Outputs screens register factories as they
    are introduced. Replacing the top screen retains Session Detail beneath the
    whole flow, so Exit can safely pop back to it.
    """

    phase: ClassVar[SessionProcessingPhase]
    COMMON_BINDINGS = [
        Binding("b,B", "back_processing", "Back", key_display="B"),
        Binding("escape", "exit_processing", "Exit", key_display="Esc"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__()
        self._session_id = session_id

    @property
    def session_id(self) -> uuid.UUID:
        """The Session being processed by this screen."""
        return self._session_id

    def compose_above_footer(self) -> ComposeResult:
        yield WorkflowRail(self.phase)

    def on_mount(self) -> None:
        self.refresh_data()

    def on_screen_resume(self) -> None:
        self.refresh_processing_state()

    def refresh_data(self) -> None:
        """Refresh shared rail state; subclasses extend this for their own content."""
        self.refresh_processing_state()

    def refresh_processing_state(self) -> None:
        """Reconcile artifact and database state, then redraw the workflow rail."""
        resolved_phase = self.application.resolve_session_processing_phase(self._session_id)
        state = self.application.session_processing_state(self._session_id)
        artifact_states = self.application.session_artifact_states(self._session_id)
        failed_phase = self._as_phase(state.failed_phase) if state is not None else None
        has_draft = state is not None and state.draft_source_artifact is not None
        rail = self.query_one(WorkflowRail)
        rail.update_workflow(
            active_phase=self.phase,
            statuses=self._workflow_statuses(
                artifact_states=artifact_states,
                resolved_phase=resolved_phase,
                failed_phase=failed_phase,
                has_draft=has_draft,
            ),
        )

    def action_back_processing(self) -> None:
        """Move one stage back without deleting completed artifacts."""
        previous_phase = {
            SessionProcessingPhase.AUDIO: None,
            SessionProcessingPhase.TRANSCRIPT: SessionProcessingPhase.AUDIO,
            SessionProcessingPhase.OUTPUTS: SessionProcessingPhase.TRANSCRIPT,
        }[self.phase]
        if previous_phase is None:
            self.action_exit_processing()
            return
        self.switch_to_processing_phase(previous_phase)

    def action_exit_processing(self) -> None:
        """Remember this stage and return to the Session Detail screen."""
        self.application.set_session_processing_phase(self._session_id, self.phase)
        self.app.pop_screen()

    def switch_to_processing_phase(self, phase: SessionProcessingPhase) -> None:
        """Persist navigation and replace only the active processing screen."""
        factory = _PROCESSING_SCREEN_FACTORIES.get(phase)
        if factory is None:
            raise RuntimeError(f"No Process screen is registered for {phase.value!r}.")
        self.application.set_session_processing_phase(self._session_id, phase)
        self.app.switch_screen(factory(self._session_id))

    def processing_succeeded(self, next_phase: SessionProcessingPhase) -> None:
        """Record a successful stage transition and refresh the shared rail."""
        self.application.clear_session_processing_failure(self._session_id)
        self.application.set_session_processing_phase(self._session_id, next_phase)
        self.refresh_processing_state()

    def processing_failed(self, message: str) -> None:
        """Persist a recoverable stage failure and refresh the shared rail."""
        self.application.record_session_processing_failure(self._session_id, self.phase, message)
        self.refresh_processing_state()

    @staticmethod
    def _as_phase(value: str | None) -> SessionProcessingPhase | None:
        try:
            return SessionProcessingPhase(value) if value is not None else None
        except ValueError:
            return None

    @staticmethod
    def _workflow_statuses(
        *,
        artifact_states: dict[ArtifactName, ArtifactStatus],
        resolved_phase: SessionProcessingPhase,
        failed_phase: SessionProcessingPhase | None,
        has_draft: bool,
    ) -> dict[SessionProcessingPhase, WorkflowStepStatus]:
        completed = {
            SessionProcessingPhase.AUDIO: (
                artifact_states[ArtifactName.INPUT_AUDIO] is ArtifactStatus.CURRENT
                and artifact_states[ArtifactName.TRANSCRIPT] is ArtifactStatus.CURRENT
            ),
            SessionProcessingPhase.TRANSCRIPT: artifact_states[ArtifactName.REVIEWED_TRANSCRIPT] is ArtifactStatus.CURRENT,
            SessionProcessingPhase.OUTPUTS: all(artifact_states[artifact] is ArtifactStatus.CURRENT for artifact in GENERATION_ORDER),
        }
        statuses: dict[SessionProcessingPhase, WorkflowStepStatus] = {}
        for phase in SessionProcessingPhase:
            if phase is failed_phase:
                statuses[phase] = WorkflowStepStatus.ERROR
            elif completed[phase]:
                statuses[phase] = WorkflowStepStatus.CURRENT
            elif phase is resolved_phase or (phase is SessionProcessingPhase.TRANSCRIPT and has_draft):
                statuses[phase] = WorkflowStepStatus.IN_PROGRESS
            else:
                statuses[phase] = WorkflowStepStatus.NOT_STARTED
        return statuses
