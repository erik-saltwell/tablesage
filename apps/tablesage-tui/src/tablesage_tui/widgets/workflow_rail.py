from __future__ import annotations

from enum import StrEnum

from tablesage_model.model import SessionProcessingPhase
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class WorkflowStepStatus(StrEnum):
    """Presentation status for a single non-interactive Process-flow stage."""

    CURRENT = "current"
    IN_PROGRESS = "in-progress"
    NOT_STARTED = "not-started"
    ERROR = "error"


_PHASE_LABELS = {
    SessionProcessingPhase.AUDIO: "Audio",
    SessionProcessingPhase.TRANSCRIPT: "Transcript",
    SessionProcessingPhase.OUTPUTS: "Outputs",
}

_STATUS_SYMBOLS = {
    WorkflowStepStatus.CURRENT: "●",
    WorkflowStepStatus.IN_PROGRESS: "◐",
    WorkflowStepStatus.NOT_STARTED: "○",
    WorkflowStepStatus.ERROR: "!",
}


class WorkflowRail(Horizontal):
    """A compact, non-focusable status display shared by Process-flow screens."""

    can_focus = False

    def __init__(self, active_phase: SessionProcessingPhase) -> None:
        super().__init__(classes="workflow-rail")
        self._active_phase = active_phase

    def compose(self) -> ComposeResult:
        for phase in SessionProcessingPhase:
            yield Static(id=f"workflow-step-{phase.value}", classes="workflow-step")

    def update_workflow(
        self,
        *,
        active_phase: SessionProcessingPhase,
        statuses: dict[SessionProcessingPhase, WorkflowStepStatus],
    ) -> None:
        """Render state symbols while styling the active screen independently."""
        self._active_phase = active_phase
        for phase in SessionProcessingPhase:
            status = statuses[phase]
            step = self.query_one(f"#workflow-step-{phase.value}", Static)
            step.update(f"{_STATUS_SYMBOLS[status]} {_PHASE_LABELS[phase]}")
            step.set_classes(
                " ".join(
                    (
                        "workflow-step",
                        f"-status-{status.value}",
                        "-active" if phase is self._active_phase else "",
                    )
                ).strip()
            )
