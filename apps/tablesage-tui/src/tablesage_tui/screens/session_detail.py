from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from tablesage_application.paths import ARTIFACTS, ArtifactCategory, ArtifactName
from tablesage_application.session_pipeline import clean_transcript, import_audio, transcribe_audio
from tablesage_application.session_pipeline.artifacts import GenerationStep
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Input, Static
from textual_fspicker import FileOpen, Filters

from ..dialogs import AttendeeDialog, AttendeeResult, ConfirmationDialog
from ..widgets import CommittingInput
from ..widgets.tablesage_header import TableSageHeader
from .artifact_export import ArtifactExportScreen
from .base import TableSageScreen
from .speaker_review import ManualReviewScreen

if TYPE_CHECKING:
    from tablesage_application.entities.sessions import Attendee

_STAGE_LABELS = {
    transcribe_audio.Stage.TRANSCRIBING: "Transcribing (this may take a while)…",
    transcribe_audio.Stage.IDENTIFYING_SPEAKERS: "Identifying speakers…",
    transcribe_audio.Stage.PUNCTUATING: "Punctuating…",
}

_CLEAN_STAGE_LABELS = {
    clean_transcript.Stage.REMOVING_BACKCHANNELS: "Removing backchannels (this may take a while)…",
    clean_transcript.Stage.ASSIGNING_ROLES: "Assigning roles…",
}

_GENERATION_STEP_LABELS = {
    GenerationStep.ROLE_TRANSCRIPT: "Role Transcript",
    GenerationStep.LEDGER: "Ledger",
    GenerationStep.SUMMARY: "Summary",
}


class SessionDetailScreen(TableSageScreen):
    """A single session's metadata, attendance, and artifact indicators."""

    section = "session detail"
    AUTO_FOCUS = ""
    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
        Binding("n,N", "new_attendee", "New", key_display="N"),
        Binding("enter,e,E", "edit_attendee", "Edit", key_display="E"),
        Binding("d,D,delete,backspace", "delete_attendee", "Delete", key_display="D"),
        Binding("i,I", "import_audio", "Imp Audio", key_display="I"),
        Binding("t,T", "transcribe_audio", "Transcribe", key_display="T"),
        Binding("r,R", "manual_review", "Review", key_display="R"),
        Binding("b,B", "generate_benchmark_transcript", "Benchmark", key_display="B"),
        Binding("c,C", "clean_transcript", "Clean Transcript", key_display="C"),
        Binding("g,G", "generate", "Generate", key_display="G"),
        Binding("x,X", "export_artifacts", "Export", key_display="X"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__()
        self._session_id = session_id
        self._session_name = ""
        self._session_date: date | None = None
        self._indicators: dict[ArtifactName, Static] = {}

    def compose_content(self) -> ComposeResult:
        with Vertical(id="session-detail-panel", classes="panel surface-2") as panel:
            panel.border_title = " session "

            with Vertical(id="session-metadata"):
                with Horizontal(classes="field-row"):
                    yield Static("Name", classes="field-label")
                    yield CommittingInput(id="session-name-input")
                with Horizontal(classes="field-row"):
                    yield Static("Date", classes="field-label")
                    yield CommittingInput(id="session-date-input", placeholder="YYYY-MM-DD")
                with Horizontal(classes="field-row"):
                    yield Static("Last Transcribed", classes="field-label")
                    yield Static("", id="session-last-transcribed-value", classes="field-value")

            with Horizontal(id="session-detail-body"):
                with Vertical(id="session-attendance-column"):
                    yield Static("Attendance", classes="section-title")
                    table: DataTable[str] = DataTable(
                        id="attendance-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
                    )
                    table.add_column("Player", key="player")
                    table.add_column("Roles", key="roles")
                    yield table

                with Vertical(id="session-indicators-column"):
                    yield Static("Artifacts", classes="section-title")
                    with Vertical(id="artifacts-panel"):
                        for name, spec in ARTIFACTS.items():
                            if not spec.should_show_in_ui:
                                continue
                            indicator = Static("")
                            self._indicators[name] = indicator
                            yield indicator

    def on_mount(self) -> None:
        self.refresh_data()

    def on_screen_resume(self) -> None:
        self._refresh_indicators()

    def refresh_data(self) -> None:
        game_session = self.application.get_session(self._session_id)
        self._session_name = game_session.name
        self._session_date = game_session.session_date

        self.query_one(TableSageHeader).campaign = game_session.name
        self.query_one("#session-name-input", CommittingInput).value = self._session_name
        self.query_one("#session-date-input", CommittingInput).value = str(self._session_date) if self._session_date else ""

        self._reload_attendance()
        self._refresh_indicators()

    # Metadata

    def on_committing_input_committed(self, event: CommittingInput.Committed) -> None:
        self._commit_metadata(event.input)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if isinstance(event.input, CommittingInput):
            event.stop()
            self._commit_metadata(event.input)
            # `Input` doesn't blur itself on Enter (unlike losing focus, which is what actually
            # triggers `CommittingInput.Committed` -- see its docstring), so without this the
            # field would keep focus indefinitely, silently swallowing every single-letter
            # binding below (I/T/R/B/C/G/X, N/E/D) as plain text instead of firing them.
            self.query_one("#attendance-table", DataTable).focus()

    def _commit_metadata(self, input_widget: CommittingInput) -> None:
        if input_widget.id == "session-name-input":
            self._commit_name(input_widget)
        elif input_widget.id == "session-date-input":
            self._commit_date(input_widget)

    def _commit_name(self, input_widget: CommittingInput) -> None:
        new_name = input_widget.value.strip()
        if not new_name or new_name == self._session_name:
            input_widget.value = self._session_name
            return

        try:
            updated = self.application.update_session(self._session_id, new_name, self._session_date)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            input_widget.value = self._session_name
            return

        self._session_name = updated.name
        self.query_one(TableSageHeader).campaign = self._session_name

    def _commit_date(self, input_widget: CommittingInput) -> None:
        raw = input_widget.value.strip()
        if not raw:
            new_date = None
        else:
            try:
                new_date = date.fromisoformat(raw)
            except ValueError:
                self.notify(f"'{raw}' isn't a valid date (expected YYYY-MM-DD).", severity="error")
                input_widget.value = str(self._session_date) if self._session_date else ""
                return

        if new_date == self._session_date:
            return

        updated = self.application.update_session(self._session_id, self._session_name, new_date)
        self._session_date = updated.session_date

    def action_pop_screen(self) -> None:
        focused = self.focused
        if isinstance(focused, CommittingInput):
            self._commit_metadata(focused)
        super().action_pop_screen()

    # Indicators / gating

    def _refresh_indicators(self) -> None:
        self._refresh_last_transcribed()
        session_artifacts = self.application.session_artifacts(self._session_id)
        for name, widget in self._indicators.items():
            present = session_artifacts[name]
            widget.update(self._indicator_text(ARTIFACTS[name].display_name, present))
            widget.set_class(not present, "artifact-missing")

        self.refresh_bindings()

    def _refresh_last_transcribed(self) -> None:
        transcript_path = self.application.session_folder(self._session_id) / ARTIFACTS[ArtifactName.TRANSCRIPT].filename
        try:
            modified_at = datetime.fromtimestamp(transcript_path.stat().st_mtime)
        except FileNotFoundError:
            value = ""
        else:
            value = modified_at.strftime("%Y-%m-%d %H:%M")
        self.query_one("#session-last-transcribed-value", Static).update(value)

    @staticmethod
    def _indicator_text(label: str, present: bool) -> str:
        # Radio-box look: a filled circle for present, a hollow one for missing
        # (color comes from the "artifact-missing" CSS class, not markup here).
        symbol = "●" if present else "○"
        return f"{symbol} {label}"

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "transcribe_audio":
            enabled, _ = self.application.can_transcribe_audio(self._session_id)
            return True if enabled else None
        if action == "manual_review":
            return True if self.application.session_artifacts(self._session_id)[ArtifactName.TRANSCRIPT] else None
        if action == "generate_benchmark_transcript":
            return True if self.application.session_artifacts(self._session_id)[ArtifactName.TRANSCRIPT] else None
        if action == "clean_transcript":
            return True if self.application.session_artifacts(self._session_id)[ArtifactName.TRANSCRIPT] else None
        if action == "generate":
            return True if self.application.next_generation_step(self._session_id) is not None else None
        if action == "export_artifacts":
            enabled, _ = self.application.can_export_artifacts(self._session_id)
            return True if enabled else None
        return True

    # Invalidation guard -- shared by every destructive edit (import audio,
    # add/remove attendee, edit roles): confirm first only if there's
    # something derived (i.e. not IMPORTED) to lose.

    def _with_invalidation_guard(self, action: Callable[[], None]) -> None:
        session_artifacts = self.application.session_artifacts(self._session_id)
        has_derived_artifact = any(
            present and ARTIFACTS[name].category is not ArtifactCategory.IMPORTED for name, present in session_artifacts.items()
        )
        if not has_derived_artifact:
            action()
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                action()

        self.app.push_screen(
            ConfirmationDialog(
                title="This Will Invalidate Processing",
                prompt="This change will delete existing derived artifacts. Continue?",
            ),
            on_confirm,
        )

    # Import audio

    def action_import_audio(self) -> None:
        def on_picked(source_path: Path | None) -> None:
            if source_path is None:
                return

            try:
                self.application.validate_import_audio_source(source_path)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return

            def do_import(*, should_clean_audio: bool) -> None:
                session_folder = self.application.session_folder(self._session_id)
                normalize_volume = self.application.settings.session_audio_import.normalize_volume
                self.run_with_progress(
                    title="Import Audio",
                    message="Cleaning audio…" if should_clean_audio else "Importing audio…",
                    work=lambda: import_audio.import_audio(
                        source_path, session_folder, normalize_volume, should_clean_audio=should_clean_audio
                    ),
                    on_success=self._after_import_audio,
                )

            if source_path.suffix.lower() == ".wav":

                def on_clean_choice(should_clean_audio: bool | None) -> None:
                    if should_clean_audio is None:
                        return
                    self._with_invalidation_guard(lambda: do_import(should_clean_audio=should_clean_audio))

                self.app.push_screen(
                    ConfirmationDialog(
                        title="Clean Audio?",
                        prompt="Run this .wav through noise-cleaning before import? Skip if it's already been cleaned.",
                    ),
                    on_clean_choice,
                )
            else:
                self._with_invalidation_guard(lambda: do_import(should_clean_audio=True))

        extensions = self.application.audio_import_extensions()
        audio_filter = Filters(
            (
                "Audio files",
                lambda path: path.suffix.lower() in extensions,
            ),
        )
        self.app.push_screen(
            FileOpen(title="Import Audio", location=Path.home(), filters=audio_filter),
            on_picked,
        )

    def _after_import_audio(self, _result: None) -> None:
        self._refresh_indicators()
        self.notify("Input audio imported.")

    # Transcribe

    def action_transcribe_audio(self) -> None:
        # No generic invalidation guard: a successful transcription replaces its transcript
        # artifacts and invalidates FROM_LOG outputs; a failed one preserves them. But if a
        # human has hand-corrected the transcript via Manual Review (R), rerunning here would
        # silently discard them -- guarded separately, by count, rather than folded into
        # `_with_invalidation_guard`'s generic wording.
        adjusted_count = self.application.count_adjusted_utterances(self._session_id)
        if adjusted_count:
            plural = "" if adjusted_count == 1 else "s"

            def on_confirm(confirmed: bool | None) -> None:
                if confirmed:
                    self._do_transcribe_audio()

            self.app.push_screen(
                ConfirmationDialog(
                    title="This Will Discard Manual Review Changes",
                    prompt=f"This will discard changes to {adjusted_count} reviewed utterance{plural}. Continue?",
                ),
                on_confirm,
            )
            return

        self._do_transcribe_audio()

    def _do_transcribe_audio(self) -> None:
        session_folder = self.application.session_folder(self._session_id)
        centroids = self.application.session_player_centroids(self._session_id)
        settings = self.application.settings

        def work() -> transcribe_audio.TranscriptionResult:
            # `embedding_factory()` loads the WeSpeaker ResNet34-LM model on first use
            # (multi-second, possibly downloading it) -- called here, on the progress dialog's
            # background thread, rather than before `run_with_progress`, so that cost is covered
            # by the dialog instead of stalling the UI before it can even appear.
            embed = self.application.embedding_factory()
            return transcribe_audio.transcribe_audio(
                session_folder,
                centroids,
                embed,
                settings.transcription_and_diarization,
                settings.speaker_identification,
                on_progress=self._on_transcribe_progress,
            )

        self.run_with_progress(
            title="Transcribe",
            message=_STAGE_LABELS[transcribe_audio.Stage.TRANSCRIBING],
            work=work,
            on_success=self._after_transcribe_audio,
        )

    def _on_transcribe_progress(self, stage: transcribe_audio.Stage, completed: int, total: int) -> None:
        self.report_stage_progress(_STAGE_LABELS[stage], completed, total)

    def _after_transcribe_audio(self, result: transcribe_audio.TranscriptionResult) -> None:
        self._refresh_indicators()
        if result.unassigned_speaker_count:
            self.notify(f"Transcribed. {result.unassigned_speaker_count} of {result.utterance_count} utterances need manual review.")
        else:
            self.notify("Transcribed.")

    # Manual review -- gated on the transcript artifact existing (see check_action).

    def action_manual_review(self) -> None:
        self.app.push_screen(ManualReviewScreen(self._session_id))

    # Benchmark transcript -- gated on the transcript artifact existing (see check_action).
    # Fast, in-memory, synchronous: no progress dialog, unlike the pipeline actions above.

    def action_generate_benchmark_transcript(self) -> None:
        result = self.application.generate_benchmark_transcript(self._session_id)
        self.notify(f"Benchmark transcript written: {result.kept_count} kept, {result.excluded_count} excluded (too short).")

    # Clean Transcript -- destructive: deletes the machine transcript and everything derived from
    # it (Reviewed Transcript, Role Transcript, benchmark, Ledger, Summary), leaving only the raw
    # input audio. Gated on the machine transcript existing (see check_action). Always confirmed,
    # since unlike every other invalidation in this screen this isn't a side effect of some other
    # edit -- it's the whole point of pressing the binding.

    def action_clean_transcript(self) -> None:
        def on_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self.application.delete_transcript(self._session_id)
            self._refresh_indicators()
            self.notify("Transcript and dependent artifacts deleted.")

        self.app.push_screen(
            ConfirmationDialog(
                title="Delete Transcript",
                prompt=(
                    "This will delete the transcript and everything generated from it -- Reviewed "
                    "Transcript, Role Transcript, benchmark, Ledger, and Summary. Continue?"
                ),
            ),
            on_confirm,
        )

    # Generate -- produces whichever of Role Transcript / Ledger / Summary this session is
    # missing next, in dependency order (see `next_generation_step`). The user can't choose which
    # one; a confirmation names the step Generate is about to run. Gated on there being a next
    # step at all (see check_action).

    def action_generate(self) -> None:
        step = self.application.next_generation_step(self._session_id)
        if step is None:
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                self._do_generate(step)

        self.app.push_screen(
            ConfirmationDialog(
                title="Generate",
                prompt=f"Generate the {_GENERATION_STEP_LABELS[step]}?",
            ),
            on_confirm,
        )

    def _do_generate(self, step: GenerationStep) -> None:
        if step is GenerationStep.ROLE_TRANSCRIPT:
            self.run_with_progress(
                title="Generate Role Transcript",
                message=_CLEAN_STAGE_LABELS[clean_transcript.Stage.REMOVING_BACKCHANNELS],
                work=lambda: self.application.clean_transcript(self._session_id, on_progress=self._on_clean_progress),
                on_success=self._after_generate_role_transcript,
            )
        elif step is GenerationStep.LEDGER:
            self.run_with_progress(
                title="Generate Ledger",
                message="Generating Ledger…",
                work=lambda: self.application.generate_ledger(self._session_id),
                on_success=self._after_generate_ledger,
            )
        elif step is GenerationStep.SUMMARY:
            self.run_with_progress(
                title="Generate Summary",
                message="Generating summary…",
                work=lambda: self.application.generate_summary(self._session_id),
                on_success=self._after_generate_summary,
            )

    def _on_clean_progress(self, stage: clean_transcript.Stage, completed: int, total: int) -> None:
        self.report_stage_progress(_CLEAN_STAGE_LABELS[stage], completed, total)

    def _after_generate_role_transcript(self, result: clean_transcript.CleanTranscriptResult) -> None:
        self._refresh_indicators()
        self.notify(f"Role Transcript generated: {result.removed_count} backchannel{'' if result.removed_count == 1 else 's'} removed.")

    def _after_generate_ledger(self, _result: None) -> None:
        self._refresh_indicators()
        self.notify("Ledger generated.")

    def _after_generate_summary(self, _result: None) -> None:
        self._refresh_indicators()
        self.notify("Summary generated.")

    # Export -- gated (see check_action).

    def action_export_artifacts(self) -> None:
        self.app.push_screen(ArtifactExportScreen(self._session_id))

    # Attendance

    def _reload_attendance(self) -> None:
        table = self.query_one("#attendance-table", DataTable)
        selected = self._selected_attendance_id()

        table.clear()
        restored_row: int | None = None
        for index, attendee in enumerate(self.application.list_attendance(self._session_id)):
            table.add_row(attendee.player_name, ", ".join(attendee.roles), key=str(attendee.attendance_id))
            if selected is not None and attendee.attendance_id == selected:
                restored_row = index

        if restored_row is not None:
            table.move_cursor(row=restored_row)

        self._refresh_indicators()

    def _selected_attendance_id(self) -> uuid.UUID | None:
        table = self.query_one("#attendance-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return uuid.UUID(row_key) if row_key else None

    def _selected_attendee(self) -> Attendee | None:
        attendance_id = self._selected_attendance_id()
        if attendance_id is None:
            return None
        return next(
            (attendee for attendee in self.application.list_attendance(self._session_id) if attendee.attendance_id == attendance_id),
            None,
        )

    def action_new_attendee(self) -> None:
        game_session = self.application.get_session(self._session_id)
        attending_ids = {attendee.player_id for attendee in self.application.list_attendance(self._session_id)}
        available = [player for _, player in self.application.list_roster(game_session.campaign_id) if player.id not in attending_ids]

        def on_saved(result: AttendeeResult | None) -> None:
            if result is None:
                return
            player_id = result.player_id
            assert player_id is not None  # allow_new_player=False below guarantees this
            roles = list(result.roles)

            def do_add() -> None:
                try:
                    self.application.add_attendance_with_roles(self._session_id, player_id, roles)
                except ValueError as exc:
                    self.notify(str(exc), severity="error")
                    return
                self._reload_attendance()

            self._with_invalidation_guard(do_add)

        self.app.push_screen(AttendeeDialog(players=available, title="Add Attendee"), on_saved)

    def action_edit_attendee(self) -> None:
        attendee = self._selected_attendee()
        if attendee is None:
            return

        game_session = self.application.get_session(self._session_id)
        attending_ids = {a.player_id for a in self.application.list_attendance(self._session_id)}
        available = [
            player
            for _, player in self.application.list_roster(game_session.campaign_id)
            if player.id not in attending_ids or player.id == attendee.player_id
        ]

        def on_saved(result: AttendeeResult | None) -> None:
            if result is None:
                return
            player_id = result.player_id
            assert player_id is not None  # allow_new_player=False below guarantees this
            roles = list(result.roles)

            def do_save() -> None:
                try:
                    if player_id != attendee.player_id:
                        self.application.set_attendance_player(self._session_id, attendee.attendance_id, player_id)
                    self.application.set_attendance_roles(self._session_id, attendee.attendance_id, roles)
                except ValueError as exc:
                    self.notify(str(exc), severity="error")
                    return
                self._reload_attendance()

            self._with_invalidation_guard(do_save)

        self.app.push_screen(
            AttendeeDialog(players=available, title="Edit Attendee", player_id=attendee.player_id, roles=list(attendee.roles)),
            on_saved,
        )

    def action_delete_attendee(self) -> None:
        attendee = self._selected_attendee()
        if attendee is None:
            return

        def on_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return

            def do_remove() -> None:
                self.application.remove_attendance(self._session_id, attendee.attendance_id)
                self._reload_attendance()

            self._with_invalidation_guard(do_remove)

        self.app.push_screen(
            ConfirmationDialog(
                title="Remove Attendee",
                prompt=f"Remove {attendee.player_name} from this session?",
            ),
            on_confirm,
        )
