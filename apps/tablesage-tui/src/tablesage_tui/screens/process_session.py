from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import widelog
from tablesage_application.paths import (
    NEW_PLAYER_STAGES,
    SessionProcessingStage,
    SessionProcessingStageID,
    artifacts_for_stage,
    get_processing_stages,
)
from tablesage_application.session_pipeline import transcribe_audio
from tablesage_application.session_pipeline.artifact_graph import ArtifactStatus, GenerationTask
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual_fspicker import Filters

from ..dialogs import ConfirmationDialog
from ..dialogs.file_picker import FileOpen
from ..widgets import ProcessingStepControl
from .base import TableSageScreen

if TYPE_CHECKING:
    from tablesage_application.session_pipeline.extract_glossary import GlossaryProposal
    from tablesage_application.session_pipeline.suggest_spelling_corrections import SpellingSuggestion
    from tablesage_tools.model import Transcript

_SKIPPED_TOOLTIP = "No new players, so this step isn't needed."

_TRANSCRIBE_LABELS = {
    transcribe_audio.Stage.TRANSCRIBING: "Transcribing (this may take a while)…",
    transcribe_audio.Stage.PUNCTUATING: "Punctuating…",
    transcribe_audio.Stage.IDENTIFYING_SPEAKERS: "Identifying speakers…",
}

# The automatic steps that have a runner (see `_run_automatic_step`).
_AUTOMATIC_STEPS = frozenset(
    {
        SessionProcessingStageID.CREATING_TRANSCRIPTION,
        SessionProcessingStageID.REMOVE_BACKCHANNELS,
        SessionProcessingStageID.ISOLATING_NEW_SPEAKERS,
        SessionProcessingStageID.SEEDING_PLAYER_VOICE_SAMPLES,
        SessionProcessingStageID.IDENTIFYING_SPEAKERS,
        SessionProcessingStageID.ASSIGN_ROLES_TO_SPEAKERS,
    }
)


def _step_control_id(stage_id: SessionProcessingStageID) -> str:
    return f"process-session-step-{stage_id.name}"


class ProcessSessionScreen(TableSageScreen):
    """Fresh starting point for the unified Session processing experience."""

    section = "process session"
    COMMON_BINDINGS = [Binding("escape", "pop_screen", "Back", key_display="Esc")]
    # Each manual step's key is shown on its control rather than in the footer.
    HIDDEN_BINDINGS = [
        Binding(stage.binding, f"run_step({int(stage.id)})", stage.action) for stage in get_processing_stages() if stage.binding is not None
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__()
        self._session_id = session_id
        self._failure: str | None = None
        # Set once this visit has started an automatic step nothing else could start (see `_complete_skipped_steps`).
        self._auto_continued = False

    @property
    def session_id(self) -> uuid.UUID:
        return self._session_id

    def on_screen_resume(self) -> None:
        self._complete_skipped_steps()

    def _complete_skipped_steps(self) -> None:
        """Complete skipped steps that are next in line, with their empty or unchanged outputs.

        A skipped step can't be started by its key, so without this a Session whose new players went
        away partway through a run could never get past it. None of these makes an LLM call when there
        are no new players.

        For the same reason, when the next step is automatic and directly follows a skipped step (e.g.
        Identify Speakers after a skipped Seed Player Voice Samples), no key could start it, so those
        automatic steps run -- once per visit, so a failing step isn't retried in a loop -- and processing
        then stops here rather than opening the next manual step, which can be started by its key.
        """
        self._refresh_steps()
        # A resume queued behind a run that has already pushed its next dialog must not race that run.
        if not self.is_current:
            return
        previous_skipped = False
        for stage in get_processing_stages():
            control = self._step_control(stage.id)
            if control.is_complete:
                previous_skipped = control.is_skipped
                continue
            if not (control.is_enabled and control.is_skipped):
                automatic = self._automatic_run_from(stage.id)
                if control.is_enabled and previous_skipped and not self._auto_continued and automatic:
                    self._auto_continued = True
                    self._log("run_after_skipped_steps", step=stage.id.name)
                    if self._check_run_credentials(automatic):
                        self._run_steps(automatic, continue_after=False)
                return
            try:
                if stage.has_manual_processing:
                    self.application.complete_processing_step_automatically(self._session_id, stage.id)
                elif stage.id is SessionProcessingStageID.ISOLATING_NEW_SPEAKERS:
                    self.application.isolate_new_speakers(self._session_id)
                else:
                    # With no new players the reviewed assignments are empty, so this only writes an empty receipt.
                    assert stage.id is SessionProcessingStageID.SEEDING_PLAYER_VOICE_SAMPLES
                    self.application.seed_player_voice_samples(self._session_id)
            except (OSError, ValueError) as exc:
                self._set_failure(f"{stage.action} failed: {exc}")
                return
            self._log("skipped_step_completed", step=stage.id.name)
            self._refresh_steps()
            if not control.is_complete:
                self._set_failure(f"{stage.action} finished without producing its output.")
                return
            previous_skipped = True

    def _log(self, op: str, **fields: object) -> None:
        """Write one log line now. Used for starts and user decisions, so a run that hangs or is
        interrupted still leaves a trail (a wide event only writes when its operation ends)."""
        with widelog.wide_event(op=f"process_session.{op}", session_id=str(self._session_id), **fields):
            pass

    def _step_control(self, stage_id: SessionProcessingStageID) -> ProcessingStepControl:
        return self.query_one(f"#{_step_control_id(stage_id)}", ProcessingStepControl)

    def _refresh_steps(self) -> None:
        """Mark each step complete when all its artifacts are current, and enabled once every earlier step is
        complete and no error blocks it or an earlier step.

        With no new players, the steps that only serve new players are shown skipped. That is display
        only: they stay incomplete until continuing processing completes them with empty outputs. Once
        Isolate New Speakers has run, its output decides instead, so steps that seeded players who are
        no longer new still show as done (see `Application.new_player_steps_skipped`).
        """
        new_players = self.application.new_players(self._session_id)
        new_player_steps_skipped = self.application.new_player_steps_skipped(self._session_id)
        self._show_new_players([player.player_name for player in new_players])
        blockers = self.application.session_processing_blockers(self._session_id)
        messages = [blocker.message for blocker in blockers]
        if self._failure is not None:
            messages.append(self._failure)
        self._show_errors(messages)
        first_blocked = min((blocker.stage for blocker in blockers), default=None)
        states = self.application.session_artifact_states(self._session_id)
        predecessors_complete = True
        for stage in get_processing_stages():
            artifacts = artifacts_for_stage(stage.id)
            is_complete = bool(artifacts) and all(states[name] is ArtifactStatus.CURRENT for name in artifacts)
            is_blocked = first_blocked is not None and stage.id >= first_blocked
            control = self._step_control(stage.id)
            control.is_complete = is_complete
            control.is_enabled = predecessors_complete and not is_blocked
            control.is_skipped = new_player_steps_skipped and stage.id in NEW_PLAYER_STAGES
            control.tooltip = _SKIPPED_TOOLTIP if control.is_skipped else None
            predecessors_complete = predecessors_complete and is_complete
        self.refresh_bindings()

    def _show_new_players(self, names: list[str]) -> None:
        text = "\n".join(f"• {name}" for name in names) if names else "All attendees have voice profiles."
        self.query_one("#process-session-new-player-list", Static).update(text)

    def _show_errors(self, messages: list[str]) -> None:
        self.query_one("#process-session-errors", Vertical).display = bool(messages)
        self.query_one("#process-session-error-list", Static).update("\n".join(f"• {message}" for message in messages))

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "run_step":
            stage_id = SessionProcessingStageID(parameters[0])
            return True if self._step_control(stage_id).can_activate else None
        return super().check_action(action, parameters)

    def action_run_step(self, stage_id: int) -> None:
        self._step_control(SessionProcessingStageID(stage_id)).press()

    def on_processing_step_control_activated(self, event: ProcessingStepControl.Activated) -> None:
        event.stop()
        for stage in get_processing_stages():
            if event.step is self._step_control(stage.id):
                self._open_step(stage.id)
                return

    def _open_step(self, stage_id: SessionProcessingStageID) -> None:
        """Start a manual step; steps that have not been built yet do nothing."""
        self._log("step_opened", step=stage_id.name)
        self._set_failure(None)
        if stage_id is SessionProcessingStageID.IMPORTING_AUDIO:
            self._start_import_audio()
        elif stage_id is SessionProcessingStageID.REVIEWING_NAME_CORRECTIONS:
            self._start_name_corrections()
        elif stage_id is SessionProcessingStageID.EXTRACTING_GLOSSARY_TERMS:
            self._start_glossary_extraction()
        elif stage_id is SessionProcessingStageID.SPELLCHECKING_GLOSSARY:
            self._start_glossary_spellcheck()
        elif stage_id is SessionProcessingStageID.GENERATING_ARTIFACTS:
            self._start_generation()
        elif stage_id is SessionProcessingStageID.REVIEWING_TRANSCRIPT:
            from .speaker_review import ManualReviewScreen

            self.app.push_screen(ManualReviewScreen(self._session_id, on_completed=self._continue_processing_later))
        elif stage_id is SessionProcessingStageID.REVIEWING_NEW_SPEAKER_ASSIGNMENTS:
            from .new_speaker_assignments import NewSpeakerAssignmentsScreen

            self.app.push_screen(NewSpeakerAssignmentsScreen(self._session_id, on_confirmed=self._continue_processing_later))

    def _continue_processing_later(self) -> None:
        """Continue from this screen's own message queue.

        Step screens call this as they close. Textual delivers a pushed screen's result to the screen that
        was handling the event when it was pushed, so opening the next step (e.g. the audio picker) from
        inside a closing screen's button handler would send the picker's result to a dead screen and
        silently drop it.
        """
        self.call_next(self._continue_processing)

    def _continue_processing(self) -> None:
        """Advance to the first incomplete step: start it when it is manual, or run the automatic steps from it.

        Continuing stops on this screen when that step is blocked, or is automatic with no runner yet.
        A manual step with nothing to review completes without its screen, and continuing goes on.
        """
        self._refresh_steps()
        for stage in get_processing_stages():
            control = self._step_control(stage.id)
            if control.is_complete:
                continue
            if not control.is_enabled:
                self._log("continue_stopped", step=stage.id.name, reason="blocked")
                return
            if stage.has_manual_processing:
                try:
                    completed = self.application.complete_processing_step_automatically(self._session_id, stage.id)
                except (OSError, ValueError) as exc:
                    self._set_failure(f"{stage.action} failed: {exc}")
                    return
                if completed:
                    self._log("step_completed_automatically", step=stage.id.name)
                    self._refresh_steps()
                    if not control.is_complete:
                        # Never loop on a step whose automatic completion didn't take.
                        self._set_failure(f"{stage.action} finished without producing its output.")
                        return
                    # Re-evaluate from the top: later steps were disabled in the snapshot taken above.
                    self._continue_processing()
                    return
                self._open_step(stage.id)
                return
            automatic = self._automatic_run_from(stage.id)
            if not automatic:
                self._log("continue_stopped", step=stage.id.name, reason="no_runner")
            elif self._check_run_credentials(automatic):
                self._run_steps(automatic)
            return
        self._log("continue_stopped", reason="all_steps_complete")

    # Import Audio (step 1) -- no screen of its own: picker, optional clean prompt, then one progress dialog
    # covering the import and the automatic steps after it.

    def _start_import_audio(self) -> None:
        automatic = self._automatic_run_from(SessionProcessingStageID.CREATING_TRANSCRIPTION)
        # Checked before the picker so a missing key never costs minutes of audio cleaning.
        if self._check_run_credentials(automatic):
            self._open_audio_picker(Path.home(), automatic)

    def _open_audio_picker(self, location: Path, automatic: list[SessionProcessingStage]) -> None:
        """The step's first screen: cancelling it returns to Process Session."""
        audio_filter = Filters(("Audio", lambda path: path.suffix.lower() in self.application.audio_import_extensions()))
        self.app.push_screen(
            FileOpen(title="Import Audio", location=location, filters=audio_filter),
            lambda source_path: self._after_audio_selected(source_path, automatic),
        )

    def _after_audio_selected(self, source_path: Path | None, automatic: list[SessionProcessingStage]) -> None:
        self._log("audio_picked", source_path=str(source_path) if source_path is not None else None, cancelled=source_path is None)
        if source_path is None:
            return
        try:
            self.application.validate_import_audio_source(source_path)
        except ValueError as exc:
            self._log("audio_rejected", source_path=str(source_path), reason=str(exc))
            self.notify(str(exc), severity="error")
            self._open_audio_picker(source_path.parent, automatic)
            return
        if source_path.suffix.lower() != ".wav":
            self._run_steps(automatic, import_source=(source_path, True))
            return

        def after_clean_prompt(should_clean: bool | None) -> None:
            self._log("clean_audio_answer", answer={True: "yes", False: "no", None: "cancel"}[should_clean])
            # Cancel goes back one screen, to the picker.
            if should_clean is None:
                self._open_audio_picker(source_path.parent, automatic)
            else:
                self._run_steps(automatic, import_source=(source_path, should_clean))

        self.app.push_screen(
            ConfirmationDialog(
                title="Clean Audio?",
                prompt="Run this .wav through noise-cleaning before import? Skip if it's already been cleaned.",
            ),
            after_clean_prompt,
        )

    # Review Name Corrections (step 2) -- the LLM call runs here, behind a progress dialog, so a failure
    # lands in the error list; the screen opens only when there is something to review.

    def _start_name_corrections(self) -> None:
        stage = next(stage for stage in get_processing_stages() if stage.id is SessionProcessingStageID.REVIEWING_NAME_CORRECTIONS)
        if not self._check_run_credentials([stage]):
            return

        def work() -> tuple[Transcript, list[SpellingSuggestion]]:
            self.report_stage_progress("Finding misheard names…", 0, 0)
            return self.application.suggest_name_corrections(self._session_id)

        self.run_with_progress(
            title=stage.action,
            message="Starting…",
            work=work,
            on_success=self._after_name_corrections_found,
            on_error=lambda exc: self._run_failed(stage.action, exc),
        )

    def _after_name_corrections_found(self, result: tuple[Transcript, list[SpellingSuggestion]]) -> None:
        transcript, suggestions = result
        self._log("name_corrections_found", suggestion_count=len(suggestions))
        if suggestions:
            from .corrections_step import CorrectionsStepScreen

            self.app.push_screen(
                CorrectionsStepScreen(
                    title="Name Corrections",
                    hint="Keep only corrections to names that were misheard; they apply to every later step.",
                    transcript=transcript,
                    suggestions=suggestions,
                    whole_words=True,
                    save=lambda corrections: self.application.save_name_corrections(self._session_id, corrections),
                    on_confirmed=self._continue_processing_later,
                )
            )
            return
        # Nothing to review: the name-corrected transcript is the cleaned one, unchanged.
        try:
            self.application.save_name_corrections(self._session_id, ())
        except (OSError, ValueError) as exc:
            self._set_failure(f"Review Name Corrections failed: {exc}")
            return
        self._continue_processing()

    # Extract Glossary Terms (step 4) -- Session Detail's Extract Glossary, run on the identified transcript so
    # the terms it adds are spellchecked against next. Like Review Name Corrections: the LLM call runs here, and
    # the review screen opens only when there is something to review.

    def _start_glossary_extraction(self) -> None:
        stage = next(stage for stage in get_processing_stages() if stage.id is SessionProcessingStageID.EXTRACTING_GLOSSARY_TERMS)
        if not self._check_run_credentials([stage]):
            return

        def work() -> list[GlossaryProposal]:
            self.report_stage_progress("Extracting glossary terms…", 0, 0)
            return self.application.suggest_glossary_terms(self._session_id)

        self.run_with_progress(
            title=stage.action,
            message="Starting…",
            work=work,
            on_success=self._after_glossary_terms_found,
            on_error=lambda exc: self._run_failed(stage.action, exc),
        )

    def _after_glossary_terms_found(self, proposals: list[GlossaryProposal]) -> None:
        self._log("glossary_terms_found", proposal_count=len(proposals))
        if proposals:
            from .glossary_review import GlossaryReviewScreen

            self.app.push_screen(
                GlossaryReviewScreen(
                    self._session_id,
                    proposals,
                    save=lambda reviewed: self.application.save_extracted_glossary_terms(self._session_id, reviewed),
                    section="process session · extract glossary terms",
                    on_complete=self._continue_processing_later,
                )
            )
            return
        # Nothing to review: complete the step with an empty receipt (a current one is left alone).
        try:
            self.application.save_extracted_glossary_terms(self._session_id, ())
        except (OSError, ValueError) as exc:
            self._set_failure(f"Extract Glossary Terms failed: {exc}")
            return
        self._continue_processing()

    # Spellcheck Against Glossary (step 5) -- like Review Name Corrections: the LLM call runs here, and the
    # screen opens only when there is something to review.

    def _start_glossary_spellcheck(self) -> None:
        stage = next(stage for stage in get_processing_stages() if stage.id is SessionProcessingStageID.SPELLCHECKING_GLOSSARY)
        if not self._check_run_credentials([stage]):
            return

        def work() -> tuple[Transcript, list[SpellingSuggestion]]:
            self.report_stage_progress("Finding misspelled glossary terms…", 0, 0)
            return self.application.suggest_glossary_spelling_corrections(self._session_id)

        self.run_with_progress(
            title=stage.action,
            message="Starting…",
            work=work,
            on_success=self._after_glossary_spellcheck_found,
            on_error=lambda exc: self._run_failed(stage.action, exc),
        )

    def _after_glossary_spellcheck_found(self, result: tuple[Transcript, list[SpellingSuggestion]]) -> None:
        transcript, suggestions = result
        self._log("glossary_spellcheck_found", suggestion_count=len(suggestions))
        if suggestions:
            from .corrections_step import CorrectionsStepScreen

            self.app.push_screen(
                CorrectionsStepScreen(
                    title="Spellcheck Against Glossary",
                    hint="Keep only corrections to glossary terms and names that were misspelled.",
                    transcript=transcript,
                    suggestions=suggestions,
                    whole_words=False,
                    save=lambda corrections: self.application.save_glossary_spelling_corrections(self._session_id, corrections),
                    on_confirmed=self._continue_processing_later,
                )
            )
            return
        # Nothing to review: the spellchecked transcript is the identified one, unchanged.
        try:
            self.application.save_glossary_spelling_corrections(self._session_id, ())
        except (OSError, ValueError) as exc:
            self._set_failure(f"Spellcheck Against Glossary failed: {exc}")
            return
        self._continue_processing()

    # Generate Artifacts (step 7) -- no screen: the shared generation runner plans the outputs, asks before
    # rebuilding earlier Sessions (Regenerate Prior or Cancel only), and runs them behind one progress dialog.

    def _start_generation(self) -> None:
        from ..generation_runner import GenerationRunner

        GenerationRunner(
            self,
            self._session_id,
            on_start=lambda: self._log("generation_started"),
            on_success=self._after_generation,
            on_error=lambda exc: self._run_failed("Generate Artifacts", exc),
            on_cancel=lambda: self._log("generation_cancelled"),
            allow_current_only=False,
        ).prepare()

    def _after_generation(self, tasks: tuple[GenerationTask, ...]) -> None:
        self._log("generation_finished", output_count=len(tasks))
        self._refresh_steps()
        if tasks:
            self.notify(f"Generated {len(tasks)} output{'' if len(tasks) == 1 else 's'}.")
            self._offer_voice_sample_enhancement()
        else:
            self.notify("All outputs are current.")

    def _offer_voice_sample_enhancement(self) -> None:
        """Offer to add this Session's voice clips to its players' profiles -- the Players screen's From Session
        action, scoped to this Session."""

        def on_dismiss(confirmed: bool | None) -> None:
            self._log("voice_sample_enhancement_answered", accepted=bool(confirmed))
            if confirmed:
                self.enhance_players_from_session(self._session_id)
            else:
                self.notify("You can add this Session's voice samples later with From Session on the Players screen.")

        self.app.push_screen(
            ConfirmationDialog(
                title="Improve Player Voice Profiles",
                prompt=(
                    "Add voice samples from this Session to your players' voice profiles? This helps TableSage "
                    "recognize them in future Sessions.\n\n"
                    "Only do this if you've carefully reviewed the transcript's speaker assignments -- "
                    "mislabeled lines will teach TableSage the wrong voice for a player."
                ),
                show_cancel=False,
                no_label="Not Now",
                yes_label="Add Samples",
            ),
            on_dismiss,
        )

    # Automatic steps

    def _automatic_run_from(self, stage_id: SessionProcessingStageID) -> list[SessionProcessingStage]:
        """The consecutive automatic steps starting at `stage_id` that have a runner."""
        run: list[SessionProcessingStage] = []
        for stage in get_processing_stages():
            if stage.id < stage_id:
                continue
            if stage.has_manual_processing or stage.id not in _AUTOMATIC_STEPS:
                break
            run.append(stage)
        return run

    def _check_run_credentials(self, stages: list[SessionProcessingStage]) -> bool:
        roles = tuple(dict.fromkeys(role for stage in stages for role in stage.llm_roles))
        transcription = any(stage.needs_transcription for stage in stages)
        ok = self.check_credentials(*roles, transcription=transcription)
        if not ok:
            self._log("credentials_missing", steps=[stage.id.name for stage in stages], llm_roles=list(roles), transcription=transcription)
        return ok

    def _run_steps(
        self, stages: list[SessionProcessingStage], *, import_source: tuple[Path, bool] | None = None, continue_after: bool = True
    ) -> None:
        """Run an optional audio import and then `stages`, in order, behind one progress dialog; then continue
        processing unless `continue_after` is False."""
        self._set_failure(None)
        running: list[str] = []
        step_names = (["IMPORTING_AUDIO"] if import_source is not None else []) + [stage.id.name for stage in stages]
        source_fields: dict[str, object] = {}
        if import_source is not None:
            source_path, should_clean = import_source
            source_fields = {"source_path": str(source_path), "should_clean_audio": should_clean}
            try:
                source_fields["source_bytes"] = source_path.stat().st_size
            except OSError as exc:
                source_fields["source_stat_error"] = str(exc)
        self._log("run_started", steps=step_names, **source_fields)

        def run_step(name: str, action: str, step: Callable[[], object], log: widelog.WideEvent) -> None:
            running.append(action)
            self._log("step_started", step=name)
            started = time.monotonic()
            self.report_progress_title(action)
            step()
            log.set(step_durations_s={name: round(time.monotonic() - started, 1)})

        def work() -> None:
            # One summary line per run: its steps, how long each took, and (automatically) any exception.
            with widelog.wide_event(op="process_session.run", session_id=str(self._session_id), steps=step_names, **source_fields) as log:
                if import_source is not None:
                    source_path, should_clean = import_source

                    def import_audio() -> None:
                        self.report_stage_progress("Cleaning audio…" if should_clean else "Importing audio…", 0, 0)
                        self.application.import_session_audio(self._session_id, source_path, should_clean_audio=should_clean)

                    run_step("IMPORTING_AUDIO", "Import Audio", import_audio, log)
                for stage in stages:
                    run_step(stage.id.name, stage.action, lambda stage_id=stage.id: self._run_automatic_step(stage_id), log)

        first_title = "Import Audio" if import_source is not None else stages[0].action
        self.run_with_progress(
            title=first_title,
            message="Starting…",
            work=work,
            on_success=lambda _result: self._after_run(stages, continue_after=continue_after),
            on_error=lambda exc: self._run_failed(running[-1] if running else first_title, exc),
        )

    def _run_automatic_step(self, stage_id: SessionProcessingStageID) -> None:
        """Run one automatic step; called on the progress worker thread."""
        if stage_id is SessionProcessingStageID.CREATING_TRANSCRIPTION:
            self.application.create_transcript(
                self._session_id,
                on_progress=lambda stage, completed, total: self.report_stage_progress(_TRANSCRIBE_LABELS[stage], completed, total),
            )
        elif stage_id is SessionProcessingStageID.REMOVE_BACKCHANNELS:
            self.report_stage_progress("Removing backchannels…", 0, 0)
            self.application.remove_bad_utterances(
                self._session_id,
                on_progress=lambda completed, total: self.report_stage_progress("Removing backchannels…", completed, total),
            )
        elif stage_id is SessionProcessingStageID.ISOLATING_NEW_SPEAKERS:
            self.application.isolate_new_speakers(self._session_id, on_progress=self.report_stage_progress)
        elif stage_id is SessionProcessingStageID.SEEDING_PLAYER_VOICE_SAMPLES:
            self.report_stage_progress("Cutting voice clips…", 0, 0)
            self.application.seed_player_voice_samples(self._session_id, on_progress=self.report_stage_progress)
        elif stage_id is SessionProcessingStageID.ASSIGN_ROLES_TO_SPEAKERS:
            self.report_stage_progress("Assigning roles…", 0, 0)
            self.application.clean_transcript(self._session_id)
        elif stage_id is SessionProcessingStageID.IDENTIFYING_SPEAKERS:
            self.report_stage_progress("Identifying speakers…", 0, 0)
            self.application.identify_session_speakers(
                self._session_id,
                on_progress=lambda stage, completed, total: self.report_stage_progress(_TRANSCRIBE_LABELS[stage], completed, total),
            )

    def _after_run(self, stages: list[SessionProcessingStage], *, continue_after: bool = True) -> None:
        self._refresh_steps()
        incomplete = [stage for stage in stages if not self._step_control(stage.id).is_complete]
        if incomplete:
            # A runner that returns without producing its artifacts must not be retried in a loop.
            self._log("step_output_missing", step=incomplete[0].id.name)
            self._set_failure(f"{incomplete[0].action} finished without producing its output.")
            return
        if continue_after:
            self._continue_processing()

    def _run_failed(self, step_name: str, exc: BaseException) -> None:
        # The run's own summary line carries the exception and traceback; this records what the user saw.
        self._log("run_failed_shown", step=step_name, message=str(exc))
        self._set_failure(f"{step_name} failed: {exc}")
        self.notify(f"{step_name} failed: {exc}", severity="error")

    def _set_failure(self, message: str | None) -> None:
        """Hold the latest run failure for the error list until processing next starts."""
        self._failure = message
        self._refresh_steps()

    def compose_content(self) -> ComposeResult:
        with Vertical(id="process-session-panel", classes="panel surface-2") as panel:
            panel.border_title = " Process Session "
            with Horizontal(id="process-session-columns"):
                with Vertical(id="process-session-steps-column"):
                    yield Static("Session Processing Actions", id="process-session-actions-header", classes="section-title")
                    with Vertical(id="process-session-steps"):
                        stages = get_processing_stages()
                        for index, stage in enumerate(stages):
                            yield ProcessingStepControl(
                                is_complete=False,
                                is_enabled=True,
                                keybinding=stage.binding,
                                entry_text=stage.action,
                                id=_step_control_id(stage.id),
                            )
                            if index < len(stages) - 1:
                                yield Static("|", classes="process-session-step-divider", markup=False)
                with Vertical(id="process-session-side-column"):
                    yield Static("New Players", id="process-session-new-players-header", classes="section-title")
                    yield Static("", id="process-session-new-player-list", markup=False)
                    with Vertical(id="process-session-errors"):
                        yield Static("Errors", id="process-session-errors-header", classes="section-title")
                        yield Static("", id="process-session-error-list", markup=False)
