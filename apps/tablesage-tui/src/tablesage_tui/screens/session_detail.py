from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date, datetime
from typing import TYPE_CHECKING, cast

from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.processing_steps import StepID
from tablesage_application.session_pipeline.artifact_graph import GENERATION_LABELS, ArtifactStatus
from tablesage_model.model import Player
from tablesage_model.player_names import validate_player_name
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Static

from ..dialogs import ArtifactRegenerationDialog, AttendeeDialog, AttendeeResult, ConfirmationDialog, SessionDialog, TextInputDialog
from ..widgets import SampleCountDataTable, sample_count_cell
from ..widgets.tablesage_header import TableSageHeader
from .artifact_export import ArtifactExportScreen
from .base import TableSageScreen

if TYPE_CHECKING:
    from tablesage_application.entities.sessions import Attendee

    from ..processing.coordinator import Run
    from .main_app import TableSageApp

_ATTENDANCE_ACTIONS = frozenset({"new_attendee", "edit_attendee", "delete_attendee"})


class SessionDetailScreen(TableSageScreen):
    """A single session's metadata, attendance, artifact indicators, and processing errors."""

    section = "session detail"
    HIDDEN_BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
    ]
    COMMON_BINDINGS = [
        Binding("p,P", "process", "Process", key_display="P"),
        Binding("x,X", "export_artifacts", "Export", key_display="X"),
        Binding("m,M", "edit_metadata", "Edit Metadata", key_display="M"),
        Binding("n,N", "new_attendee", "New Attendee", key_display="N"),
        Binding("enter,e,E", "edit_attendee", "Edit Attendee", key_display="E"),
        Binding("d,D,delete,backspace", "delete_attendee", "Delete Attendee", key_display="D"),
    ]
    OTHER_BINDINGS = [
        Binding("r,R", "regenerate", "Regenerate Artifact", key_display="R"),
        Binding("c,C", "clean_session", "Clean Session", key_display="C"),
        Binding("l,L", "extract_glossary", "Extract Glossary", key_display="L"),
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
                    yield Static("", id="session-name-value", classes="field-value")
                with Horizontal(classes="field-row"):
                    yield Static("Date", classes="field-label")
                    yield Static("", id="session-date-value", classes="field-value")
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
        cast("TableSageApp", self.app).coordinator.subscribe(self._on_run_event)
        self.refresh_data()

    def on_unmount(self) -> None:
        cast("TableSageApp", self.app).coordinator.unsubscribe(self._on_run_event)

    def on_screen_resume(self) -> None:
        self._refresh_indicators()

    def _on_run_event(self, run: Run, event: str) -> None:
        if event == "run_stopped" and run.session_id == self._session_id and self.is_current:
            self._refresh_indicators()

    def refresh_data(self) -> None:
        game_session = self.application.get_session(self._session_id)
        self._session_name = game_session.name
        self._session_date = game_session.session_date

        self.query_one(TableSageHeader).campaign = game_session.name
        self._update_metadata_display()

        self._reload_attendance()
        self._refresh_indicators()

    # Metadata

    def _update_metadata_display(self) -> None:
        self.query_one("#session-name-value", Static).update(self._session_name)
        self.query_one("#session-date-value", Static).update(str(self._session_date) if self._session_date else "")

    def action_edit_metadata(self) -> None:
        self.app.push_screen(
            SessionDialog(
                title="Edit Metadata",
                name=self._session_name,
                session_date=self._session_date,
                submit_label="Save",
                on_submit=self._submit_metadata,
            )
        )

    async def _submit_metadata(self, name: str, session_date: date | None) -> str | None:
        # Session folders are numbered slots, not name-derived, so unlike Player and Campaign
        # there's no folder-collision check on a rename here.
        try:
            updated = self.application.update_session(self._session_id, name, session_date)
        except ValueError as exc:
            return str(exc)
        self._session_name = updated.name
        self._session_date = updated.session_date
        self.query_one(TableSageHeader).campaign = self._session_name
        self._update_metadata_display()
        return None

    # Indicators / gating

    def _refresh_indicators(self) -> None:
        self._refresh_last_transcribed()
        artifact_states = self._artifact_states()
        for name, widget in self._indicators.items():
            status = artifact_states[name]
            widget.update(self._indicator_text(ARTIFACTS[name].display_name, status))
            widget.tooltip = self._indicator_tooltip(name, status)
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
    def _indicator_tooltip(name: ArtifactName, status: ArtifactStatus) -> str:
        if status is ArtifactStatus.MISSING:
            if name is ArtifactName.INPUT_AUDIO:
                return "Missing: Input audio hasn't been imported yet. Process the Session to import it."
            return "Missing: This artifact hasn't been created yet. Process the Session to create it."
        if status is ArtifactStatus.CURRENT:
            return "Current: This artifact is up to date with its inputs."
        return "Out of date: This artifact exists but needs processing again before it is current."

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

    def _run_forced_generation(self, artifact: ArtifactName) -> None:
        """Regenerate `artifact` and everything downstream of it, as a processing run (so it can't overlap another)."""
        self._clear_errors()
        coordinator = cast("TableSageApp", self.app).coordinator
        if coordinator.is_running:
            self.notify("Processing is already running.", severity="warning")
            return
        self.application.reopen_artifact(self._session_id, artifact)
        coordinator.advance(self._session_id, trigger="session_detail:regenerate", facts={"force": artifact})

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
        if cast("TableSageApp", self.app).coordinator.is_running:
            self.notify("Wait for processing to finish before cleaning this Session.", severity="warning")
            return

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

    # Extract Glossary -- a processing run that restarts Suggest Glossary Terms, so its review, the glossary commit,
    # and everything the new terms affect follow as usual.

    def action_extract_glossary(self) -> None:
        cast("TableSageApp", self.app).coordinator.advance(
            self._session_id, trigger="session_detail:extract_glossary", restart=StepID.SUGGEST_GLOSSARY_TERMS
        )

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
