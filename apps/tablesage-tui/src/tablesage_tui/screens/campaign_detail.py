from __future__ import annotations

import uuid

from tablesage_model.model import GAME_MASTER_ROLE, GlossaryEntry
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.widgets import ContentSwitcher, DataTable, Input, Static

from ..dialogs import (
    ConfirmationDialog,
    GlossaryEntryDialog,
    PlayerPickerDialog,
    RolePickerDialog,
    TextInputDialog,
)
from ..widgets import CommittingInput
from ..widgets.tablesage_header import TableSageHeader
from .base import TableSageScreen
from .session_detail import SessionDetailScreen

_TABS = ("roster", "sessions", "glossary")


class CampaignDetailScreen(TableSageScreen):
    """A single campaign's metadata plus its roster, sessions, and glossary."""

    section = "campaign detail"
    AUTO_FOCUS = ""
    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc"),
        Binding("r,R", "show_roster", "Roster", key_display="R"),
        Binding("s,S", "show_sessions", "Sessions", key_display="S"),
        Binding("g,G", "show_glossary", "Glossary", key_display="G"),
        Binding("n,N", "new_item", "New", key_display="N"),
        Binding("enter,e,E", "edit_item", "Edit", key_display="E"),
        Binding("d,D,delete,backspace", "delete_item", "Delete", key_display="D"),
        Binding("c,C", "cleanup", "Clean up", key_display="C"),
    ]

    def __init__(self, campaign_id: uuid.UUID) -> None:
        super().__init__()
        self._campaign_id = campaign_id
        self._campaign_name = ""
        self._description: str | None = None
        self._game_system: str | None = None
        self._active_tab = "sessions"

    def compose_content(self) -> ComposeResult:
        with Vertical(id="campaign-detail-panel", classes="panel surface-2") as panel:
            panel.border_title = " campaign "

            with Vertical(id="campaign-metadata"):
                with Horizontal(classes="field-row"):
                    yield Static("Name", classes="field-label")
                    yield CommittingInput(id="campaign-name-input")
                with Horizontal(classes="field-row"):
                    yield Static("Description", classes="field-label")
                    yield CommittingInput(id="campaign-description-input", placeholder="Optional description")
                with Horizontal(classes="field-row"):
                    yield Static("Game System", classes="field-label")
                    yield CommittingInput(id="campaign-game-system-input", placeholder="Optional game system")

            with Horizontal(id="campaign-detail-tabs"):
                yield Static("[R] Roster", id="tab-label-roster", classes="tab-label")
                yield Static("[S] Sessions", id="tab-label-sessions", classes="tab-label")
                yield Static("[G] Glossary", id="tab-label-glossary", classes="tab-label")

            with ContentSwitcher(id="campaign-detail-switcher", initial="sessions-tab"):
                with Vertical(id="roster-tab"):
                    roster_table: DataTable[str] = DataTable(
                        id="roster-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
                    )
                    roster_table.add_column("Player", key="player")
                    roster_table.add_column("Default Role", key="role")
                    yield roster_table
                with Vertical(id="sessions-tab"):
                    sessions_table: DataTable[str] = DataTable(
                        id="sessions-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
                    )
                    sessions_table.add_column("#", key="sequence")
                    sessions_table.add_column("Name", key="name")
                    sessions_table.add_column("Date", key="date")
                    sessions_table.add_column("Status", key="status")
                    yield sessions_table
                with Vertical(id="glossary-tab"):
                    glossary_table: DataTable[str] = DataTable(
                        id="glossary-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
                    )
                    glossary_table.add_column("Term", key="term")
                    glossary_table.add_column("Description", key="description")
                    yield glossary_table

    def on_mount(self) -> None:
        self._reload_metadata_and_tables()
        self._set_active_tab("sessions")

    def on_screen_resume(self) -> None:
        self._reload_metadata_and_tables()

    def refresh_data(self) -> None:
        self._reload_metadata_and_tables()

    def _reload_metadata_and_tables(self) -> None:
        campaign = self.application.get_campaign(self._campaign_id)
        self._campaign_name = campaign.name
        self._description = campaign.description
        self._game_system = campaign.game_system

        self.query_one(TableSageHeader).campaign = self._campaign_name
        self.query_one("#campaign-name-input", CommittingInput).value = self._campaign_name
        self.query_one("#campaign-description-input", CommittingInput).value = self._description or ""
        self.query_one("#campaign-game-system-input", CommittingInput).value = self._game_system or ""

        self._reload_roster()
        self._reload_sessions()
        self._reload_glossary()

    # Metadata

    def on_committing_input_committed(self, event: CommittingInput.Committed) -> None:
        self._commit_metadata(event.input)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if isinstance(event.input, CommittingInput):
            event.stop()
            self._commit_metadata(event.input)

    def _commit_metadata(self, input_widget: CommittingInput) -> None:
        if input_widget.id == "campaign-name-input":
            self._commit_name(input_widget)
        elif input_widget.id in ("campaign-description-input", "campaign-game-system-input"):
            self._commit_description_and_game_system()

    def _commit_name(self, input_widget: CommittingInput) -> None:
        new_name = input_widget.value.strip()
        if not new_name or new_name == self._campaign_name:
            input_widget.value = self._campaign_name
            return

        try:
            renamed = self.application.rename_campaign(self._campaign_id, new_name)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            input_widget.value = self._campaign_name
            return

        self._campaign_name = renamed.name
        self.query_one(TableSageHeader).campaign = self._campaign_name

    def _commit_description_and_game_system(self) -> None:
        description = self.query_one("#campaign-description-input", CommittingInput).value.strip() or None
        game_system = self.query_one("#campaign-game-system-input", CommittingInput).value.strip() or None
        if description == self._description and game_system == self._game_system:
            return
        updated = self.application.update_campaign(self._campaign_id, description, game_system)
        self._description = updated.description
        self._game_system = updated.game_system

    def action_pop_screen(self) -> None:
        focused = self.focused
        if isinstance(focused, CommittingInput):
            self._commit_metadata(focused)
        super().action_pop_screen()

    # Tabs

    def action_show_roster(self) -> None:
        self._set_active_tab("roster")

    def action_show_sessions(self) -> None:
        self._set_active_tab("sessions")

    def action_show_glossary(self) -> None:
        self._set_active_tab("glossary")

    def on_click(self, event: Click) -> None:
        widget = event.widget
        if widget is None or widget.id is None or not widget.id.startswith("tab-label-"):
            return
        self._set_active_tab(widget.id.removeprefix("tab-label-"))

    def _set_active_tab(self, tab: str) -> None:
        self._active_tab = tab
        self.query_one("#campaign-detail-switcher", ContentSwitcher).current = f"{tab}-tab"
        for name in _TABS:
            self.query_one(f"#tab-label-{name}", Static).set_class(name == tab, "-active")
        self.refresh_bindings()
        self.query_one(f"#{tab}-table", DataTable).focus()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "cleanup":
            return self._active_tab == "sessions"
        return True

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_edit_item()

    def _selected_row_id(self, table_id: str) -> uuid.UUID | None:
        table = self.query_one(f"#{table_id}", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return uuid.UUID(row_key) if row_key else None

    # Roster

    def _reload_roster(self) -> None:
        table = self.query_one("#roster-table", DataTable)
        table.clear()
        for membership, player in self.application.list_roster(self._campaign_id):
            table.add_row(player.name, self._role_label(membership.default_role_name), key=str(membership.id))

    @staticmethod
    def _role_label(default_role_name: str) -> str:
        return "Game Master" if default_role_name == GAME_MASTER_ROLE else default_role_name

    def _new_roster_member(self) -> None:
        rostered_ids = {player.id for _, player in self.application.list_roster(self._campaign_id)}
        available = [player for player in self.application.list_players() if player.id not in rostered_ids]

        def after_player_picked(player_id: uuid.UUID | None) -> None:
            if player_id is None:
                return
            player_name = next((player.name for player in available if player.id == player_id), "")

            def after_role_picked(role: str | None) -> None:
                if role is None:
                    return
                try:
                    self.application.add_player_to_campaign(self._campaign_id, player_id, role)
                except ValueError as exc:
                    self.notify(str(exc), severity="error")
                    return
                self._reload_roster()

            self.app.push_screen(RolePickerDialog(player_name=player_name), after_role_picked)

        self.app.push_screen(PlayerPickerDialog(players=available), after_player_picked)

    def _edit_roster_member(self) -> None:
        membership_id = self._selected_row_id("roster-table")
        if membership_id is None:
            return

        membership, player = next(((m, p) for m, p in self.application.list_roster(self._campaign_id) if m.id == membership_id))

        def after_role_picked(role: str | None) -> None:
            if role is None:
                return
            self.application.update_default_role(membership_id, role)
            self._reload_roster()

        self.app.push_screen(
            RolePickerDialog(player_name=player.name, current_role=self._role_label(membership.default_role_name)),
            after_role_picked,
        )

    def _delete_roster_member(self) -> None:
        membership_id = self._selected_row_id("roster-table")
        if membership_id is None:
            return

        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self.application.remove_from_roster(membership_id)
            self._reload_roster()

        self.app.push_screen(
            ConfirmationDialog(
                title="Remove From Roster",
                prompt="Remove this player from the campaign roster? Their profile and other memberships are unaffected.",
            ),
            on_dismiss,
        )

    # Sessions

    def _reload_sessions(self) -> None:
        table = self.query_one("#sessions-table", DataTable)
        table.clear()
        sessions = sorted(self.application.list_sessions(self._campaign_id), key=lambda session: session.sequence_number)
        for session in sessions:
            table.add_row(
                f"{session.sequence_number:03d}",
                session.name,
                str(session.session_date) if session.session_date else "",
                session.status,
                key=str(session.id),
            )

    def _new_session(self) -> None:
        def on_dismiss(name: str | None) -> None:
            if name is None:
                return
            try:
                created = self.application.create_session(self._campaign_id, name)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self.app.push_screen(SessionDetailScreen(created.id))

        self.app.push_screen(
            TextInputDialog(title="New Session", prompt="Enter a name", placeholder="Session name", submit_label="Create Session"),
            on_dismiss,
        )

    def _open_session(self) -> None:
        session_id = self._selected_row_id("sessions-table")
        if session_id is None:
            return
        self.app.push_screen(SessionDetailScreen(session_id))

    def _delete_session(self) -> None:
        session_id = self._selected_row_id("sessions-table")
        if session_id is None:
            return

        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self.application.delete_session(session_id)
            self._reload_sessions()

        self.app.push_screen(
            ConfirmationDialog(title="Delete Session", prompt="Permanently delete this session, its attendance, and its roles?"),
            on_dismiss,
        )

    def action_cleanup(self) -> None:
        if self._active_tab != "sessions":
            return

        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            removed = self.application.cleanup_orphan_session_dirs(self._campaign_id)
            if removed:
                self.notify(f"Removed {len(removed)} orphan session folder(s): {', '.join(removed)}.")
            else:
                self.notify("No orphan session folders found.")

        self.app.push_screen(
            ConfirmationDialog(
                title="Clean Up Sessions",
                prompt="Remove session folders on disk that have no matching session in the database?",
            ),
            on_dismiss,
        )

    # Glossary

    def _reload_glossary(self) -> None:
        table = self.query_one("#glossary-table", DataTable)
        table.clear()
        for entry in self.application.list_glossary_entries(self._campaign_id):
            table.add_row(entry.term, entry.description or "", key=str(entry.id))

    def _new_glossary_entry(self) -> None:
        def on_dismiss(result: tuple[str, str | None] | None) -> None:
            if result is None:
                return
            term, description = result
            try:
                self.application.create_glossary_entry(GlossaryEntry(campaign_id=self._campaign_id, term=term, description=description))
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self._reload_glossary()

        self.app.push_screen(GlossaryEntryDialog(title="New Glossary Entry", submit_label="Create Entry"), on_dismiss)

    def _edit_glossary_entry(self) -> None:
        entry_id = self._selected_row_id("glossary-table")
        if entry_id is None:
            return

        entry = next(
            (entry for entry in self.application.list_glossary_entries(self._campaign_id) if entry.id == entry_id),
            None,
        )
        if entry is None:
            return

        def on_dismiss(result: tuple[str, str | None] | None) -> None:
            if result is None:
                return
            term, description = result
            try:
                self.application.update_glossary_entry(self._campaign_id, entry_id, term, description)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self._reload_glossary()

        self.app.push_screen(
            GlossaryEntryDialog(
                title="Edit Glossary Entry",
                term=entry.term,
                description=entry.description or "",
                submit_label="Save",
            ),
            on_dismiss,
        )

    def _delete_glossary_entry(self) -> None:
        entry_id = self._selected_row_id("glossary-table")
        if entry_id is None:
            return

        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self.application.delete_glossary_entry(self._campaign_id, entry_id)
            self._reload_glossary()

        self.app.push_screen(ConfirmationDialog(title="Delete Glossary Entry", prompt="Delete this glossary entry?"), on_dismiss)

    # Dispatch

    def action_new_item(self) -> None:
        if self._active_tab == "roster":
            self._new_roster_member()
        elif self._active_tab == "glossary":
            self._new_glossary_entry()
        else:
            self._new_session()

    def action_edit_item(self) -> None:
        if self._active_tab == "roster":
            self._edit_roster_member()
        elif self._active_tab == "glossary":
            self._edit_glossary_entry()
        else:
            self._open_session()

    def action_delete_item(self) -> None:
        if self._active_tab == "roster":
            self._delete_roster_member()
        elif self._active_tab == "glossary":
            self._delete_glossary_entry()
        else:
            self._delete_session()
