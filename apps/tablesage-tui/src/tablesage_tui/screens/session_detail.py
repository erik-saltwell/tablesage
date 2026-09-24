from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date, datetime
from typing import TYPE_CHECKING

from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.artifact_graph import GENERATION_LABELS, ArtifactStatus, GenerationTask
from tablesage_application.session_pipeline.extract_glossary import GlossaryProposal
from tablesage_model.model import Player
from tablesage_model.player_names import validate_player_name
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Input, Static

from ..dialogs import ArtifactRegenerationDialog, AttendeeDialog, AttendeeResult, ConfirmationDialog, TextInputDialog
from ..generation_runner import GenerationRunner
from ..widgets import CommittingInput, SampleCountDataTable, sample_count_cell
from ..widgets.tablesage_header import TableSageHeader
from .artifact_export import ArtifactExportScreen
from .base import TableSageScreen
from .glossary_review import GlossaryReviewScreen

if TYPE_CHECKING:
    from tablesage_application.entities.sessions import Attendee

_ATTENDANCE_ACTIONS = frozenset({"new_attendee", "edit_attendee", "delete_attendee"})


class SessionDetailScreen(TableSageScreen):
    """A single session's metadata, attendance, artifact indicators, and processing errors."""

    section = "session detail"
    AUTO_FOCUS = "#attendance-table"
    HIDDEN_BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
    ]
    COMMON_BINDINGS = [
        Binding("n,N", "new_attendee", "New Player", key_display="N"),
        Binding("enter,e,E", "edit_attendee", "Edit Player", key_display="E"),
        Binding("d,D,delete,backspace", "delete_attendee", "Delete Player", key_display="D"),
        Binding("p,P", "process", "Process", key_display="P"),
    ]
    OTHER_BINDINGS = [
        Binding("r,R", "regenerate", "Regenerate Artifact", key_display="R"),
        Binding("c,C", "clean_session", "Clean Session", key_display="C"),
        Binding("l,L", "extract_glossary", "Extract Glossary", key_display="L"),
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
                    with Vertical(id="attendance-section"):
                        yield Static("Attendance", classes="section-title")
                        attendance_table = SampleCountDataTable(
                            id="attendance-table",
                            cursor_type="row",
                            zebra_stripes=True,
                            classes="tablesage-table",
                            zero_sample_tooltip="No samples for this player yet. Processing will add samples.",
                        )
                        attendance_table.add_column("Samples", key="samples")
                        attendance_table.add_column("Player", key="player")
                        attendance_table.add_column("Roles", key="roles")
                        yield attendance_table

                    with Vertical(id="errors-section"):
                        yield Static("Errors", classes="section-title")
                        error_table: DataTable[str] = DataTable(
                            id="error-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
                        )
                        error_table.add_column("Action", key="action")
                        error_table.add_column("Error", key="error")
                        yield error_table

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
            # binding below (A/R/B/G/C/X, N/E/D) as plain text instead of firing them.
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
        artifact_states = self._artifact_states()
        for name, widget in self._indicators.items():
            status = artifact_states[name]
            widget.update(self._indicator_text(ARTIFACTS[name].display_name, status))
            widget.set_class(status is ArtifactStatus.MISSING, "artifact-missing")
            widget.set_class(status is ArtifactStatus.STALE, "artifact-stale")

        self.refresh_bindings()

    def _artifact_states(self) -> dict[ArtifactName, ArtifactStatus]:
        """Read computed states, retaining compatibility with lightweight UI test doubles."""
        states = self.application.session_artifact_states(self._session_id)
        if isinstance(states, dict) and all(isinstance(value, ArtifactStatus) for value in states.values()):
            return states
        return {
            name: ArtifactStatus.CURRENT if present else ArtifactStatus.MISSING
            for name, present in self.application.session_artifacts(self._session_id).items()
        }

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
    def _indicator_text(label: str, status: ArtifactStatus) -> str:
        symbol = {
            ArtifactStatus.CURRENT: "●",
            ArtifactStatus.STALE: "◐",
            ArtifactStatus.MISSING: "○",
        }[status]
        return f"{symbol} {label}"

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in _ATTENDANCE_ACTIONS:
            if self.focused is not self.query_one("#attendance-table", DataTable):
                return None
            if action in ("edit_attendee", "delete_attendee") and self._selected_attendee() is None:
                return None
            return True
        if action == "process":
            return True
        if action == "regenerate":
            states = self._artifact_states()
            return True if states[ArtifactName.REVIEWED_TRANSCRIPT] is ArtifactStatus.CURRENT else None
        if action == "clean_session":
            enabled, _ = self.application.can_clean_session(self._session_id)
            return True if enabled else None
        if action == "extract_glossary":
            enabled, _ = self.application.can_extract_glossary(self._session_id)
            return True if enabled else None
        if action == "export_artifacts":
            enabled, _ = self.application.can_export_artifacts(self._session_id)
            return True if enabled else None
        return True

    # Errors -- a table-shaped record for specialist actions that remain on Session Detail,
    # including forced regeneration and Clean Session. Process-flow failures are persisted and
    # displayed by their stage screens instead.

    def _clear_errors(self) -> None:
        self.query_one("#error-table", DataTable).clear()

    def _record_error(self, action_label: str, message: str) -> None:
        self.query_one("#error-table", DataTable).add_row(action_label, message)
        self.notify(message, severity="error")

    # Process is the only primary entry point for the three-stage workflow.

    def action_process(self) -> None:
        self._start_processing()

    def _start_processing(self) -> None:
        from .process_session import ProcessSessionScreen

        self.app.push_screen(ProcessSessionScreen(self._session_id))

    def _after_forced_generation(self, result: tuple[GenerationTask, ...]) -> None:
        self._refresh_indicators()
        self.notify("Outputs generated." if result else "All outputs are current.")

    def _run_forced_generation(self, artifact: ArtifactName) -> None:
        runner = GenerationRunner(
            self,
            self._session_id,
            on_start=self._clear_errors,
            on_success=self._after_forced_generation,
            on_error=lambda exc: self._record_error("Regenerate Artifact", str(exc)),
        )
        runner.prepare(force=artifact)

    def action_regenerate(self) -> None:
        def on_selected(selected: ArtifactName | None) -> None:
            if selected is None:
                return

            def on_confirm(confirmed: bool | None) -> None:
                if confirmed:
                    self._run_forced_generation(selected)

            self.app.push_screen(
                ConfirmationDialog(
                    title="Regenerate Artifact",
                    prompt=f"Regenerate {GENERATION_LABELS[selected]} and update stale downstream outputs?",
                ),
                on_confirm,
            )

        self.app.push_screen(ArtifactRegenerationDialog(), on_selected)

    # Clean Session -- destructive: deletes every artifact for this session, including the raw
    # input audio. Gated on there being anything to delete (see check_action). Always confirmed,
    # since unlike every other invalidation in this screen this isn't a side effect of some other
    # edit -- it's the whole point of pressing the binding.

    def action_clean_session(self) -> None:
        self._clear_errors()

        def on_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return
            try:
                self.application.clean_session(self._session_id)
            except Exception as exc:
                self._record_error("Clean Session", str(exc))
                return
            self._refresh_indicators()
            self.notify("All artifacts deleted.")

        self.app.push_screen(
            ConfirmationDialog(
                title="Clean Session",
                prompt="This will permanently delete every artifact for this session, including the input audio. Continue?",
            ),
            on_confirm,
        )

    # Extract Glossary -- independent of Generate and gated on a Role Transcript.

    def action_extract_glossary(self) -> None:
        self.run_with_progress(
            title="Extract Glossary",
            message="Extracting glossary terms…",
            work=lambda: self.application.extract_glossary(self._session_id),
            on_success=self._after_extract_glossary,
        )

    def _after_extract_glossary(self, proposals: list[GlossaryProposal]) -> None:
        if not proposals:
            self.notify("No new glossary terms found.")
            return
        self.app.push_screen(GlossaryReviewScreen(self._session_id, proposals))

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
            table.add_row(
                sample_count_cell(self.application.get_player(attendee.player_id).sample_count),
                attendee.player_name,
                ", ".join(attendee.roles),
                key=str(attendee.attendance_id),
            )
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
        def show(player_id: uuid.UUID | None = None, roles: tuple[str, ...] = ()) -> None:
            attending_ids = {attendee.player_id for attendee in self.application.list_attendance(self._session_id)}
            available = [player for player in self.application.list_players() if player.id not in attending_ids]

            def on_saved(result: AttendeeResult | None) -> None:
                if result is None:
                    return
                if result.create_player:
                    self._create_player(lambda player: show(player.id, result.roles))
                    return
                new_player_id = result.player_id
                assert new_player_id is not None  # allow_new_player=False below guarantees this
                try:
                    self.application.add_attendance_with_roles(self._session_id, new_player_id, list(result.roles))
                except ValueError as exc:
                    self.notify(str(exc), severity="error")
                    return
                self._reload_attendance()

            self.app.push_screen(AttendeeDialog(players=available, title="Add Attendee", player_id=player_id, roles=list(roles)), on_saved)

        show()

    def _create_player(self, on_created: Callable[[Player], None]) -> None:
        """Prompt for a name, create the player, then call `on_created` with it."""

        def on_named(name: str | None) -> None:
            if not name:
                return
            try:
                validate_player_name(name)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return

            def proceed() -> None:
                try:
                    player = self.application.create_player(Player(name=name))
                except (ValueError, OSError) as exc:
                    self.notify(str(exc), severity="error")
                    return
                on_created(player)

            self.run_with_folder_collision_check(
                title="Player Folder Exists",
                prompt=(
                    f"A player folder named '{name}' already exists on disk. "
                    "This may be left over from a previously deleted player. Delete it and continue?"
                ),
                exists=lambda: self.application.player_folder_exists(name),
                delete_existing=lambda: self.application.delete_orphan_player_folder(name),
                proceed=proceed,
            )

        self.app.push_screen(
            TextInputDialog(title="New Player", prompt="Enter a player name", placeholder="Player name", submit_label="Create Player"),
            on_named,
        )

    def action_edit_attendee(self) -> None:
        attendee = self._selected_attendee()
        if attendee is None:
            return

        current_player_id = attendee.player_id

        def show(player_id: uuid.UUID, roles: tuple[str, ...]) -> None:
            attending_ids = {a.player_id for a in self.application.list_attendance(self._session_id)}
            available = [
                player for player in self.application.list_players() if player.id not in attending_ids or player.id == current_player_id
            ]

            def on_saved(result: AttendeeResult | None) -> None:
                if result is None:
                    return
                if result.create_player:
                    self._create_player(lambda player: show(player.id, result.roles))
                    return
                new_player_id = result.player_id
                assert new_player_id is not None  # allow_new_player=False below guarantees this
                try:
                    if new_player_id != attendee.player_id:
                        self.application.set_attendance_player(self._session_id, attendee.attendance_id, new_player_id)
                    self.application.set_attendance_roles(self._session_id, attendee.attendance_id, list(result.roles))
                except ValueError as exc:
                    self.notify(str(exc), severity="error")
                    return
                self._reload_attendance()

            self.app.push_screen(AttendeeDialog(players=available, title="Edit Attendee", player_id=player_id, roles=list(roles)), on_saved)

        show(current_player_id, attendee.roles)

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

            do_remove()

        self.app.push_screen(
            ConfirmationDialog(
                title="Remove Attendee",
                prompt=f"Remove {attendee.player_name} from this session?",
            ),
            on_confirm,
        )
