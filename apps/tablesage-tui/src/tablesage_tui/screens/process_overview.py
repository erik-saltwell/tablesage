from __future__ import annotations

import uuid

from tablesage_model.model import SessionProcessingPhase
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from ..widgets import CommandButton
from .base import TableSageScreen


class ProcessSessionOverviewScreen(TableSageScreen):
    """Checkpoint-oriented entry point for the expanded session process flow."""

    section = "process session"

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__()
        self._session_id = session_id

    def compose_content(self) -> ComposeResult:
        with Vertical(classes="panel surface-2") as panel:
            panel.border_title = " process session "
            yield Static("", id="process-overview-status")
            with CommandButton("import_audio", id="process-import", classes="call-to-action"):
                yield Static("1  Import Audio")
            with CommandButton("review_bootstrap", id="process-bootstrap"):
                yield Static("2  Review Bootstrap Candidates")
            yield Static("✓  Identify All Speakers", id="process-identify")
            with CommandButton("review_new_speakers", id="process-new-speakers"):
                yield Static("3  Review New-Speaker Assignments")
            with CommandButton("spellcheck", id="process-spelling"):
                yield Static("4  Spellcheck Against Glossary")
            with CommandButton("review_transcript", id="process-transcript"):
                yield Static("5  Review Transcript")
            with CommandButton("generate", id="process-generate"):
                yield Static("Generate Artifacts")

    def on_mount(self) -> None:
        self._refresh()

    def on_screen_resume(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        phase = self.application.resolve_session_processing_phase(self._session_id)
        labels = {
            SessionProcessingPhase.AUDIO: "Ready to import audio.",
            SessionProcessingPhase.BOOTSTRAP_REVIEW: "Ready to review bootstrap candidates.",
            SessionProcessingPhase.NEW_SPEAKER_REVIEW: "Speaker identification is ready for review.",
            SessionProcessingPhase.SPELLING: "Ready for spelling review.",
            SessionProcessingPhase.TRANSCRIPT: "Ready for transcript review.",
            SessionProcessingPhase.OUTPUTS: "Ready to generate artifacts.",
        }
        self.query_one("#process-overview-status", Static).update(labels[phase])
        enabled = {
            "process-import": phase is SessionProcessingPhase.AUDIO,
            "process-bootstrap": phase is SessionProcessingPhase.BOOTSTRAP_REVIEW,
            "process-new-speakers": phase is SessionProcessingPhase.NEW_SPEAKER_REVIEW,
            "process-spelling": phase is SessionProcessingPhase.SPELLING,
            "process-transcript": phase is SessionProcessingPhase.TRANSCRIPT,
            "process-generate": phase is SessionProcessingPhase.OUTPUTS,
        }
        for widget_id, value in enabled.items():
            self.query_one(f"#{widget_id}", CommandButton).disabled = not value
        self.query_one("#process-identify", Static).display = phase is not SessionProcessingPhase.BOOTSTRAP_REVIEW

    def action_import_audio(self) -> None:
        from .audio_processing import AudioProcessingScreen

        self.app.push_screen(AudioProcessingScreen(self._session_id))

    def action_review_bootstrap(self) -> None:
        from .bootstrap_review import BootstrapCandidateReviewScreen

        self.app.push_screen(BootstrapCandidateReviewScreen(self._session_id))

    def action_review_new_speakers(self) -> None:
        from .bootstrap_review import NewSpeakerReviewScreen

        self.app.push_screen(NewSpeakerReviewScreen(self._session_id))

    def action_spellcheck(self) -> None:
        from .speaker_review import ManualReviewScreen

        self.app.push_screen(ManualReviewScreen(self._session_id))

    def action_review_transcript(self) -> None:
        from .speaker_review import ManualReviewScreen

        self.app.push_screen(ManualReviewScreen(self._session_id))

    def action_generate(self) -> None:
        from .outputs_processing import OutputsProcessingScreen

        self.app.push_screen(OutputsProcessingScreen(self._session_id))
