from __future__ import annotations

import uuid
from pathlib import Path

from tablesage_application.paths import ArtifactName
from tablesage_application.previously_on import CampaignHistory, Ingredients
from tablesage_application.session_pipeline.artifact_graph import (
    GENERATION_LABELS,
    ArtifactStatus,
    GenerationTask,
)
from tablesage_model.model import GlossaryEntry
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.widgets import ContentSwitcher, DataTable, Input, Static

from ..dialogs import (
    ConfirmationDialog,
    GlossaryEntryDialog,
    TextInputDialog,
)
from ..dialogs.file_picker import FileSave
from ..widgets import CommittingInput
from ..widgets.tablesage_header import TableSageHeader
from .base import TableSageScreen
from .session_detail import SessionDetailScreen

_TABS = ("sessions", "glossary")


class CampaignDetailScreen(TableSageScreen):
    """A single campaign's metadata, sessions, and glossary."""

    section = "campaign detail"
    AUTO_FOCUS = "#campaign-name-input"
    HIDDEN_BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
    ]
    COMMON_BINDINGS = [
        Binding("s,S", "show_sessions", "Sessions", key_display="S"),
        Binding("g,G", "show_glossary", "Glossary", key_display="G"),
        Binding("n,N", "new_session_item", "New Session", key_display="N"),
        Binding("n,N", "new_glossary_item", "New Entry", key_display="N"),
        Binding("enter,e,E", "edit_session_item", "Edit Session", key_display="E"),
        Binding("enter,e,E", "edit_glossary_item", "Edit Entry", key_display="E"),
        Binding("d,D,delete,backspace", "delete_session_item", "Delete Session", key_display="D"),
        Binding("d,D,delete,backspace", "delete_glossary_item", "Delete Entry", key_display="D"),
    ]
    OTHER_BINDINGS = [
        Binding("x,X", "export_campaign", "Export Campaign", key_display="X"),
        Binding("c,C", "cleanup", "Clean Up", key_display="C"),
        Binding("o,O", "regenerate_all_outputs", "Regenerate All Outputs", key_display="O"),
        Binding("y,Y", "generate_opportunities", "Generate Opportunities", key_display="Y"),
        Binding("v,V", "create_previously_on", "Create Previously On", key_display="V"),
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
                yield Static("[S] Sessions", id="tab-label-sessions", classes="tab-label")
                yield Static("[G] Glossary", id="tab-label-glossary", classes="tab-label")

            with ContentSwitcher(id="campaign-detail-switcher", initial="sessions-tab"):
                with Vertical(id="sessions-tab"):
                    sessions_table: DataTable[str] = DataTable(
                        id="sessions-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
                    )
                    sessions_table.add_column("#", key="sequence")
                    sessions_table.add_column("Name", key="name")
                    sessions_table.add_column("Date", key="date")
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
        self._set_active_tab("sessions", focus_table=False)

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

        def proceed() -> None:
            try:
                renamed = self.application.rename_campaign(self._campaign_id, new_name)
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                input_widget.value = self._campaign_name
                return
            self._campaign_name = renamed.name
            self.query_one(TableSageHeader).campaign = self._campaign_name

        def on_cancel() -> None:
            input_widget.value = self._campaign_name

        self.run_with_folder_collision_check(
            title="Campaign Folder Exists",
            prompt=(
                f"A campaign folder named '{new_name}' already exists on disk. "
                "This may be left over from a previously deleted campaign. Delete it and continue?"
            ),
            exists=lambda: self.application.campaign_folder_exists(new_name),
            delete_existing=lambda: self.application.delete_orphan_campaign_folder(new_name),
            proceed=proceed,
            on_cancel=on_cancel,
        )

    def _commit_description_and_game_system(self) -> None:
        description = self.query_one("#campaign-description-input", CommittingInput).value.strip() or None
        game_system = self.query_one("#campaign-game-system-input", CommittingInput).value.strip() or None
        if description == self._description and game_system == self._game_system:
            return
        updated = self.application.update_campaign(self._campaign_id, description, game_system)
        self._description = updated.description
        self._game_system = updated.game_system

    def action_pop_screen(self) -> None:
        # The name field has focus on open, so Esc first leaves a field for the table (losing focus commits
        # it) and the letter shortcuts start working; Esc from anywhere else goes back.
        if isinstance(self.focused, CommittingInput):
            self.query_one(f"#{self._active_tab}-table", DataTable).focus()
            return
        super().action_pop_screen()

    # Tabs

    def action_show_sessions(self) -> None:
        self._set_active_tab("sessions")

    def action_show_glossary(self) -> None:
        self._set_active_tab("glossary")

    def on_click(self, event: Click) -> None:
        widget = event.widget
        if widget is None or widget.id is None or not widget.id.startswith("tab-label-"):
            return
        self._set_active_tab(widget.id.removeprefix("tab-label-"))

    def _set_active_tab(self, tab: str, *, focus_table: bool = True) -> None:
        self._active_tab = tab
        self.query_one("#campaign-detail-switcher", ContentSwitcher).current = f"{tab}-tab"
        for name in _TABS:
            self.query_one(f"#tab-label-{name}", Static).set_class(name == tab, "-active")
        self.refresh_bindings()
        if focus_table:
            self.query_one(f"#{tab}-table", DataTable).focus()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "show_sessions":
            return True if self._active_tab != "sessions" else False
        if action == "show_glossary":
            return True if self._active_tab != "glossary" else False
        if action in {"new_session_item", "new_glossary_item"}:
            expected_tab = "sessions" if action == "new_session_item" else "glossary"
            return True if self._active_tab == expected_tab else False
        if action in {
            "edit_session_item",
            "edit_glossary_item",
            "delete_session_item",
            "delete_glossary_item",
        }:
            expected_tab = "sessions" if action.endswith("session_item") else "glossary"
            if self._active_tab != expected_tab:
                return False
            return True if self._selected_row_id(f"{self._active_tab}-table") is not None else None
        return True

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        if self._active_tab == "glossary":
            self.action_edit_glossary_item()
        else:
            self.action_edit_session_item()

    def _selected_row_id(self, table_id: str) -> uuid.UUID | None:
        table = self.query_one(f"#{table_id}", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return uuid.UUID(row_key) if row_key else None

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
                key=str(session.id),
            )
        self.refresh_bindings()

    def _new_session(self) -> None:
        def on_dismiss(name: str | None) -> None:
            if name is None:
                return

            def proceed() -> None:
                try:
                    created = self.application.create_session(self._campaign_id, name)
                except ValueError as exc:
                    self.notify(str(exc), severity="error")
                    return
                self.app.push_screen(SessionDetailScreen(created.id))

            self.run_with_folder_collision_check(
                title="Session Folder Exists",
                prompt=(
                    "A session folder already exists in this campaign's next slot on disk. "
                    "This may be left over from a previously deleted session. Delete it and continue?"
                ),
                exists=lambda: self.application.session_folder_would_collide(self._campaign_id),
                delete_existing=lambda: self.application.delete_colliding_session_folder(self._campaign_id),
                proceed=proceed,
            )

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
        self.refresh_bindings()

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

    def action_export_campaign(self) -> None:
        def is_busy() -> bool:
            sessions = self.application.list_sessions(self._campaign_id)
            session_ids = {session.id for session in sessions}
            return any(session.status == "processing" for session in sessions) or any(
                worker.is_running
                and (
                    getattr(worker.node, "_campaign_id", None) == self._campaign_id
                    or getattr(worker.node, "_session_id", None) in session_ids
                )
                for worker in self.app.workers
            )

        if is_busy():
            self.notify("Wait for campaign processing to finish before exporting.", severity="error")
            return

        def on_picked(destination: Path | None) -> None:
            if destination is None:
                return
            if is_busy():
                self.notify("Wait for campaign processing to finish before exporting.", severity="error")
                return
            self.run_with_progress(
                title="Export Campaign",
                message="Copying the database and campaign files…",
                work=lambda: self.application.export_campaign(self._campaign_id, destination),
                on_success=lambda _: self.notify(f"Exported campaign to {destination}."),
            )

        self.app.push_screen(
            FileSave(title="Export Campaign", location=Path.home(), default_file="campaign.zip"),
            on_picked,
        )

    def action_regenerate_all_outputs(self) -> None:
        """Run the same stale-aware output generation as ``G`` for reviewed audio sessions."""
        sessions = sorted(self.application.list_sessions(self._campaign_id), key=lambda item: item.sequence_number)
        audio_sessions = [
            game_session for game_session in sessions if self.application.session_artifacts(game_session.id)[ArtifactName.INPUT_AUDIO]
        ]
        ready_sessions = [
            game_session
            for game_session in audio_sessions
            if self.application.session_artifact_states(game_session.id)[ArtifactName.REVIEWED_TRANSCRIPT] is ArtifactStatus.CURRENT
        ]
        pending_review_count = len(audio_sessions) - len(ready_sessions)
        if not audio_sessions:
            self.notify("No sessions have imported audio.")
            return
        if not ready_sessions:
            self.notify("Imported-audio sessions must have a completed current transcript review before outputs can be generated.")
            return

        def work() -> tuple[GenerationTask, ...]:
            completed_sessions = 0
            generated: list[GenerationTask] = []
            total_sessions = len(ready_sessions)
            for game_session in ready_sessions:
                session_label = f"Session {game_session.sequence_number:03d}"
                self.report_stage_progress(f"{session_label}: checking outputs…", completed_sessions, total_sessions)
                generated.extend(
                    self.application.generate_outputs(
                        game_session.id,
                        on_stage=lambda task, _completed, _total, session_label=session_label, completed_sessions=completed_sessions: (
                            self.report_stage_progress(
                                f"{session_label}: {GENERATION_LABELS[task.artifact_name]}…",
                                completed_sessions,
                                total_sessions,
                            )
                        ),
                    )
                )
                completed_sessions += 1
                self.report_stage_progress(f"{session_label}: complete", completed_sessions, total_sessions)
            return tuple(generated)

        def on_success(generated: tuple[GenerationTask, ...]) -> None:
            self._reload_metadata_and_tables()
            message = f"Regenerated {len(generated)} output phase(s) across {len(ready_sessions)} session(s)."
            if pending_review_count:
                message += f" Skipped {pending_review_count} session(s) awaiting transcript review."
            self.notify(message)

        self.run_with_progress(
            title="Regenerate All Outputs",
            message="Checking session outputs…",
            work=work,
            on_success=on_success,
        )

    def action_generate_opportunities(self) -> None:
        from tablesage_application.campaign_recap import CampaignSceneRecap

        from .opportunities import OpportunitiesScreen

        def open_opportunities(recap: CampaignSceneRecap) -> None:
            self.app.push_screen(OpportunitiesScreen(recap))

        self.run_with_progress(
            title="Generate Opportunities",
            message="Checking Campaign Scene Breakdowns…",
            work=lambda: self.application.create_campaign_scene_recap(self._campaign_id),
            on_success=open_opportunities,
        )

    def action_create_previously_on(self) -> None:
        from .previously_on import PreviouslyOnScreen

        def prepare() -> tuple[CampaignHistory, Ingredients]:
            history = self.application.previously_on_history(self._campaign_id)
            ingredients = self.application.previously_on_ingredients(history)
            return history, ingredients

        def open_flow(result: tuple[CampaignHistory, Ingredients]) -> None:
            self.app.push_screen(PreviouslyOnScreen(*result))

        self.run_with_progress(
            title="Create Previously On",
            message="Checking Scene Breakdowns and recalling Campaign ingredients…",
            work=prepare,
            on_success=open_flow,
        )

    # Dispatch

    def action_new_session_item(self) -> None:
        self._new_session()

    def action_new_glossary_item(self) -> None:
        self._new_glossary_entry()

    def action_edit_session_item(self) -> None:
        self._open_session()

    def action_edit_glossary_item(self) -> None:
        self._edit_glossary_entry()

    def action_delete_session_item(self) -> None:
        self._delete_session()

    def action_delete_glossary_item(self) -> None:
        self._delete_glossary_entry()
