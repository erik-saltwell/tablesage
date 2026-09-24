from __future__ import annotations

import uuid
from collections.abc import Callable

from tablesage_application.paths import ArtifactName
from tablesage_application.session_pipeline import clean_transcript
from tablesage_application.session_pipeline.artifact_graph import GenerationTask

from .dialogs import ConfirmationDialog
from .screens.base import TableSageScreen

_STAGE_MESSAGES = {
    ArtifactName.ROLE_TRANSCRIPT: "Removing leftover backchannels…",
    ArtifactName.TRANSCRIPT_SECTIONS: "Generating Transcript Sections…",
    ArtifactName.LEDGER: "Generating Ledger and Scene Breakdown…",
    ArtifactName.PLAYER_INTRODUCTIONS: "Generating Player Introductions…",
    ArtifactName.RECAP_SUMMARY: "Generating Recap Summary…",
    ArtifactName.SUMMARY: "Generating Summary…",
}


class GenerationRunner:
    """Shared TUI orchestration for ordinary generation and forced regeneration."""

    def __init__(
        self,
        screen: TableSageScreen,
        session_id: uuid.UUID,
        *,
        on_start: Callable[[], None],
        on_success: Callable[[tuple[GenerationTask, ...]], None],
        on_error: Callable[[BaseException], None],
        on_cancel: Callable[[], None] | None = None,
        allow_current_only: bool = True,
    ) -> None:
        self._screen = screen
        self._session_id = session_id
        self._on_start = on_start
        self._on_success = on_success
        self._on_error = on_error
        self._on_cancel = on_cancel
        # Process Session's Generate Artifacts step offers only Regenerate Prior or Cancel.
        self._allow_current_only = allow_current_only

    def prepare(self, *, force: ArtifactName | None = None) -> None:
        """Plan work, ask about stale prior Sessions when needed, then run it."""
        try:
            plan = self._screen.application.generation_plan(self._session_id, force=force)
        except Exception as exc:
            self._on_error(exc)
            return

        prior_tasks = tuple(task for task in plan if task.session_id != self._session_id)
        if not prior_tasks:
            self._run(force=force)
            return

        prior_session_count = len({task.session_id for task in prior_tasks})
        phase_label = "phase" if len(prior_tasks) == 1 else "phases"
        session_label = "Session" if prior_session_count == 1 else "Sessions"

        def on_choice(choice: bool | None) -> None:
            if choice is True:
                self._run(force=force)
            elif choice is False and self._allow_current_only:
                self._run(force=force, rebuild_prior_sessions=False)
            elif self._on_cancel is not None:
                self._on_cancel()

        requirement = (
            f"This action requires rebuilding {len(prior_tasks)} output {phase_label} in {prior_session_count} prior {session_label}.\n\n"
        )
        if self._allow_current_only:
            dialog = ConfirmationDialog(
                title="Prior Sessions Are Out of Date",
                prompt=requirement + "Regenerate Prior rebuilds them first. Current Only processes this Session and places a note "
                "in the Summary instead of including a stale prior recap. Cancel does nothing.",
                yes_label="Regenerate Prior",
                no_label="Current Only",
            )
        else:
            dialog = ConfirmationDialog(
                title="Prior Sessions Are Out of Date",
                prompt=requirement + "Regenerate Prior rebuilds them first, then this Session. Cancel does nothing.",
                show_cancel=False,
                yes_label="Regenerate Prior",
                no_label="Cancel",
            )
        self._screen.app.push_screen(dialog, on_choice)

    def _run(self, *, force: ArtifactName | None = None, rebuild_prior_sessions: bool = True) -> None:
        if not self._screen.check_credentials("llm_model_high"):
            if self._on_cancel is not None:
                self._on_cancel()
            return
        self._on_start()

        def work() -> tuple[GenerationTask, ...]:
            return self._screen.application.generate_outputs(
                self._session_id,
                force=force,
                rebuild_prior_sessions=rebuild_prior_sessions,
                on_stage=lambda task, _completed, _total: self._screen.report_stage_progress(_STAGE_MESSAGES[task.artifact_name], 0, 0),
                on_clean_progress=self._on_clean_progress,
            )

        self._screen.run_with_progress(
            title="Generate Outputs",
            message=_STAGE_MESSAGES[ArtifactName.ROLE_TRANSCRIPT],
            work=work,
            on_success=self._on_success,
            on_error=self._on_error,
        )

    def _on_clean_progress(self, stage: clean_transcript.Stage, completed: int, total: int) -> None:
        message = {
            clean_transcript.Stage.REMOVING_BACKCHANNELS: "Removing leftover backchannels…",
            clean_transcript.Stage.ASSIGNING_ROLES: "Assigning roles…",
        }[stage]
        self._screen.report_stage_progress(message, completed, total)
