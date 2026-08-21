from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Input, Static
from textual_fspicker import FileOpen, Filters

from ..dialogs import AttendeeDialog, AttendeeResult, ConfirmationDialog
from ..widgets import CommittingInput
from ..widgets.tablesage_header import TableSageHeader
from .base import TableSageScreen

if TYPE_CHECKING:
    from tablesage_application.entities.sessions import Attendee


class SessionDetailScreen(TableSageScreen):
    """A single session's metadata, attendance, and artifact indicators."""

    section = "session detail"
    AUTO_FOCUS = ""
    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
        Binding("n,N", "new_attendee", "Add Attendee", key_display="N"),
        Binding("enter,e,E", "edit_attendee", "Edit Attendee", key_display="E"),
        Binding("d,D,delete,backspace", "delete_attendee", "Remove Attendee", key_display="D"),
        Binding("i,I", "import_audio", "Import Audio", key_display="I"),
        Binding("p,P", "process_session", "Process", key_display="P"),
        Binding("g,G", "generate_summary", "Generate Summary", key_display="G"),
    ]

    def __init__(self, session_id: uuid.UUID) -> None:
        super().__init__()
        self._session_id = session_id
        self._session_name = ""
        self._session_date: date | None = None

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
                    yield Static("Status", classes="field-label")
                    yield Static("", id="session-status-value", classes="field-value")

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
                        yield Static("", id="indicator-input-audio")
                        yield Static("", id="indicator-processed-session")
                        yield Static("", id="indicator-summary")

    def on_mount(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        game_session = self.application.get_session(self._session_id)
        self._session_name = game_session.name
        self._session_date = game_session.session_date

        self.query_one(TableSageHeader).campaign = game_session.name
        self.query_one("#session-name-input", CommittingInput).value = self._session_name
        self.query_one("#session-date-input", CommittingInput).value = str(self._session_date) if self._session_date else ""
        self.query_one("#session-status-value", Static).update(game_session.status)

        self._reload_attendance()
        self._refresh_indicators()

    # Metadata

    def on_committing_input_committed(self, event: CommittingInput.Committed) -> None:
        self._commit_metadata(event.input)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if isinstance(event.input, CommittingInput):
            event.stop()
            self._commit_metadata(event.input)

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
        artifacts = self.application.session_artifacts(self._session_id)
        self._set_indicator("#indicator-input-audio", "Input Audio", artifacts.has_input_audio)
        self._set_indicator("#indicator-processed-session", "Processed Session", artifacts.has_processed_session)
        self._set_indicator("#indicator-summary", "Session Summary", artifacts.has_summary)

        self.refresh_bindings()

    def _set_indicator(self, widget_id: str, label: str, present: bool) -> None:
        widget = self.query_one(widget_id, Static)
        widget.update(self._indicator_text(label, present))
        widget.set_class(not present, "artifact-missing")

    @staticmethod
    def _indicator_text(label: str, present: bool) -> str:
        # Radio-box look: a filled circle for present, a hollow one for missing
        # (color comes from the "artifact-missing" CSS class, not markup here).
        symbol = "●" if present else "○"
        return f"{symbol} {label}"

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "process_session":
            enabled, _ = self.application.can_process_session(self._session_id)
            return True if enabled else None
        if action == "generate_summary":
            enabled, _ = self.application.can_generate_summary(self._session_id)
            return True if enabled else None
        return True

    # Invalidation guard -- shared by every destructive edit (import audio,
    # add/remove attendee, edit roles): confirm first only if there's
    # something to lose.

    def _with_invalidation_guard(self, action: Callable[[], None]) -> None:
        artifacts = self.application.session_artifacts(self._session_id)
        if not (artifacts.has_processed_session or artifacts.has_summary):
            action()
            return

        def on_confirm(confirmed: bool | None) -> None:
            if confirmed:
                action()

        self.app.push_screen(
            ConfirmationDialog(
                title="This Will Invalidate Processing",
                prompt="This change will delete the existing processed session and/or summary. Continue?",
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

            def do_import() -> None:
                self.run_with_progress(
                    title="Import Audio",
                    message="Cleaning audio…",
                    work=lambda: self.application.import_session_audio(self._session_id, source_path),
                    on_success=self._after_import_audio,
                )

            self._with_invalidation_guard(do_import)

        extensions = self.application.audio_import_extensions()
        audio_filter = Filters(
            (
                f"Audio files ({', '.join(sorted(extensions))})",
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

    # Process / Generate -- gated (see check_action), but the pipeline itself
    # is stubbed until Phases 11/12.

    def action_process_session(self) -> None:
        self.notify("Processing a session is coming soon.")

    def action_generate_summary(self) -> None:
        self.notify("Generating a summary is coming soon.")

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

            def do_add() -> None:
                try:
                    self.application.add_attendance_with_roles(self._session_id, result.player_id, list(result.roles))
                except ValueError as exc:
                    self.notify(str(exc), severity="error")
                    return
                self._reload_attendance()

            self._with_invalidation_guard(do_add)

        self.app.push_screen(AttendeeDialog(players=available, attendee=None), on_saved)

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

            def do_save() -> None:
                try:
                    if result.player_id != attendee.player_id:
                        self.application.set_attendance_player(self._session_id, attendee.attendance_id, result.player_id)
                    self.application.set_attendance_roles(self._session_id, attendee.attendance_id, list(result.roles))
                except ValueError as exc:
                    self.notify(str(exc), severity="error")
                    return
                self._reload_attendance()

            self._with_invalidation_guard(do_save)

        self.app.push_screen(AttendeeDialog(players=available, attendee=attendee), on_saved)

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
