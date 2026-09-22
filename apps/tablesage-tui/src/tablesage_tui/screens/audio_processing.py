from __future__ import annotations

import uuid
from pathlib import Path

from tablesage_application.paths import ArtifactName
from tablesage_application.session_pipeline import transcribe_audio
from tablesage_application.session_pipeline.artifact_graph import ArtifactStatus
from tablesage_application.session_pipeline.bootstrap_workflow import BootstrapEligibility
from tablesage_model.model import SessionProcessingPhase
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Static
from textual_fspicker import Filters

from ..dialogs import ConfirmationDialog
from ..dialogs.file_picker import FileOpen
from .process_overview import ProcessSessionOverviewScreen
from .session_processing import SessionProcessingScreen, register_processing_screen
from .speaker_review import ManualReviewScreen

_STAGE_LABELS = {
    transcribe_audio.Stage.TRANSCRIBING: "Transcribing (this may take a while)…",
    transcribe_audio.Stage.IDENTIFYING_SPEAKERS: "Identifying speakers…",
    transcribe_audio.Stage.PUNCTUATING: "Punctuating…",
    transcribe_audio.Stage.REMOVING_BACKCHANNELS: "Removing backchannels (this may take a while)…",
}


class AudioProcessingScreen(SessionProcessingScreen):
    """Import or replace Session audio, then advance to transcript review."""

    section = "process · audio"
    phase = SessionProcessingPhase.AUDIO
    AUTO_FOCUS = "#audio-add-button"
    COMMON_BINDINGS = [
        *SessionProcessingScreen.COMMON_BINDINGS,
        Binding("a,A", "choose_audio", "Add Audio", key_display="A"),
        Binding("r,R", "retry_transcription", "Retry Transcription", key_display="R"),
        Binding("c,C", "continue_to_transcript", "Continue", key_display="C"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__(session_id)
        self._importing_audio = False

    def compose_content(self) -> ComposeResult:
        with Vertical(id="audio-processing-panel", classes="panel surface-2") as panel:
            panel.border_title = " audio "
            yield Static("", id="audio-processing-status")
            yield Static("", id="audio-processing-error", classes="processing-error")
            yield Button("Add Audio", id="audio-add-button", variant="primary")
            yield Button("Retry Transcription", id="audio-retry-button")
            yield Button("Continue to Transcript", id="audio-continue-button")

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one("#audio-add-button", Button).focus()

    def refresh_data(self) -> None:
        super().refresh_data()
        states = self.application.session_artifact_states(self.session_id)
        has_audio = states[ArtifactName.INPUT_AUDIO] is ArtifactStatus.CURRENT
        has_transcript = states[ArtifactName.TRANSCRIPT] is ArtifactStatus.CURRENT
        status = self.query_one("#audio-processing-status", Static)
        if has_transcript:
            status.update("Audio and machine transcript are ready. Continue to review the transcript.")
        elif has_audio:
            status.update("Audio is imported, but transcription needs to be retried.")
        else:
            status.update("Add an audio recording to begin processing this Session.")

        self.query_one("#audio-add-button", Button).label = "Replace Audio" if has_audio else "Add Audio"
        self.query_one("#audio-retry-button", Button).disabled = not has_audio or has_transcript
        self.query_one("#audio-continue-button", Button).disabled = not has_transcript
        state = self.application.session_processing_state(self.session_id)
        error = ""
        if state is not None and state.failed_phase == self.phase.value:
            error = state.failure_message or ""
        self.query_one("#audio-processing-error", Static).update(error)
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        states = self.application.session_artifact_states(self.session_id)
        has_audio = states[ArtifactName.INPUT_AUDIO] is ArtifactStatus.CURRENT
        has_transcript = states[ArtifactName.TRANSCRIPT] is ArtifactStatus.CURRENT
        if action == "retry_transcription":
            return True if has_audio and not has_transcript else None
        if action == "continue_to_transcript":
            return True if has_transcript else None
        return super().check_action(action, parameters)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "audio-add-button":
            self.action_choose_audio()
        elif event.button.id == "audio-retry-button":
            self.action_retry_transcription()
        elif event.button.id == "audio-continue-button":
            self.action_continue_to_transcript()

    def action_choose_audio(self) -> None:
        audio_filter = Filters(("Audio files", lambda path: path.suffix.lower() in self.application.audio_import_extensions()))
        self.app.push_screen(
            FileOpen(title="Add Audio", location=Path.home(), filters=audio_filter),
            self._after_audio_selected,
        )

    def _after_audio_selected(self, source_path: Path | None) -> None:
        if source_path is None:
            return
        try:
            self.application.validate_import_audio_source(source_path)
        except ValueError as exc:
            self._report_audio_failure(str(exc))
            return

        state = self.application.session_processing_state(self.session_id)
        if state is not None and state.draft_source_artifact is not None:
            self.app.push_screen(
                ConfirmationDialog(
                    title="Replace Audio?",
                    prompt=("Saved transcript edits will no longer match the replacement audio and will be discarded. Replace the audio?"),
                    no_label="Cancel",
                    yes_label="Replace Audio",
                ),
                lambda confirmed: self._choose_cleaning(source_path) if confirmed else None,
            )
            return
        self._choose_cleaning(source_path)

    def _choose_cleaning(self, source_path: Path) -> None:
        if source_path.suffix.lower() != ".wav":
            self._import_and_transcribe(source_path, should_clean_audio=True)
            return
        self.app.push_screen(
            ConfirmationDialog(
                title="Clean Audio?",
                prompt="Run this .wav through noise-cleaning before import? Skip if it's already been cleaned.",
            ),
            lambda should_clean: (
                self._import_and_transcribe(source_path, should_clean_audio=should_clean) if should_clean is not None else None
            ),
        )

    def _import_and_transcribe(self, source_path: Path, *, should_clean_audio: bool) -> None:
        if not self.check_credentials("llm_model_lite", transcription=True):
            return
        self.application.clear_session_processing_failure(self.session_id)
        self.refresh_processing_state()
        self._importing_audio = True
        self.run_with_progress(
            title="Import Audio",
            message="Cleaning audio…" if should_clean_audio else "Importing audio…",
            work=lambda: self._prepare_after_import(source_path, should_clean_audio),
            on_success=self._after_transcription,
            on_error=lambda exc: self._report_audio_failure(str(exc)),
        )

    def action_retry_transcription(self) -> None:
        if not self.check_credentials("llm_model_lite", transcription=True):
            return
        self.application.clear_session_processing_failure(self.session_id)
        self.refresh_processing_state()
        self._importing_audio = False
        self.run_with_progress(
            title="Retry Transcription",
            message="Transcribing (this may take a while)…",
            work=self._retry_preparation,
            on_success=self._after_transcription,
            on_error=lambda exc: self._report_audio_failure(str(exc)),
        )

    def _on_transcribe_progress(self, stage: transcribe_audio.Stage, completed: int, total: int) -> None:
        self.report_stage_progress(_STAGE_LABELS[stage], completed, total)

    def _prepare_after_import(self, source_path: Path, should_clean_audio: bool) -> object:
        eligibility = self.application.bootstrap_eligibility(self.session_id)
        if not (type(eligibility) is BootstrapEligibility and isinstance(eligibility.targets, tuple) and eligibility.targets):
            return self.application.import_and_transcribe_audio(
                self.session_id,
                source_path,
                should_clean_audio=should_clean_audio,
                on_progress=self._on_transcribe_progress,
            )
        self.application.import_session_audio(self.session_id, source_path, should_clean_audio=should_clean_audio)
        return self._retry_preparation()

    def _retry_preparation(self) -> object:
        eligibility = self.application.bootstrap_eligibility(self.session_id)
        if type(eligibility) is BootstrapEligibility and isinstance(eligibility.targets, tuple) and eligibility.targets:
            return self.application.prepare_session_bootstrap(self.session_id, on_progress=self._on_transcribe_progress)
        return self.application.transcribe_session_audio(self.session_id, on_progress=self._on_transcribe_progress)

    def _after_transcription(self, result: object) -> None:
        if not isinstance(result, transcribe_audio.TranscriptionResult):
            self.processing_succeeded(SessionProcessingPhase.BOOTSTRAP_REVIEW)
            self.notify("Audio prepared. Review the proposed bootstrap candidates.")
            self.app.switch_screen(ProcessSessionOverviewScreen(self.session_id))
            return
        self.processing_succeeded(SessionProcessingPhase.TRANSCRIPT)
        message = "Audio imported and transcribed." if self._importing_audio else "Audio transcribed."
        if result.unassigned_speaker_count:
            message += f" {result.unassigned_speaker_count} of {result.utterance_count} utterances need manual review."
        if result.removed_backchannel_count:
            plural = "" if result.removed_backchannel_count == 1 else "s"
            message += f" {result.removed_backchannel_count} backchannel{plural} removed."
        self.notify(message)
        self.app.switch_screen(ManualReviewScreen(self.session_id))

    def _report_audio_failure(self, message: str) -> None:
        self.processing_failed(message)
        self.refresh_data()
        self.notify(message, severity="error")

    def action_continue_to_transcript(self) -> None:
        self.application.set_session_processing_phase(self.session_id, SessionProcessingPhase.TRANSCRIPT)
        self.app.switch_screen(ManualReviewScreen(self.session_id))


register_processing_screen(SessionProcessingPhase.AUDIO, AudioProcessingScreen)
