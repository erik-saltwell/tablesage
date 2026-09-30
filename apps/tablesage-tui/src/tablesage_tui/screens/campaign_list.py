from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

from rich.text import Text
from tablesage_model.model import Campaign
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Resize
from textual.widgets import DataTable
from textual_fspicker import Filters

from ..dialogs import CampaignDialog, ConfirmationDialog
from ..dialogs.file_picker import FileOpen, FileSave
from ..dialogs.player_archive_errors import PlayerArchiveErrorsDialog
from .base import TableSageScreen
from .campaign_detail import CampaignDetailScreen

_GAME_SYSTEM_WIDTH = 20
_LAST_SESSION_WIDTH = 14
_MIN_CAMPAIGN_WIDTH = 20
_COLUMN_PADDING_SLACK = 8


class CampaignListScreen(TableSageScreen):
    """Shown when at least one campaign exists."""

    section = "campaigns"
    HIDDEN_BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
    ]
    COMMON_BINDINGS = [
        Binding("n,N", "new_campaign", "New Campaign", key_display="N"),
        Binding("enter,e,E", "open_campaign", "Edit Campaign", key_display="E"),
        Binding("d,D,delete,backspace", "delete_campaign", "Delete Campaign", key_display="D"),
    ]
    OTHER_BINDINGS = [
        Binding("c,C", "cleanup_campaigns", "Clean Up", key_display="C"),
        Binding("x,X", "export_campaign", "Export Campaign", key_display="X"),
        Binding("i,I", "import_campaign", "Import Campaign", key_display="I"),
    ]

    def compose_content(self) -> ComposeResult:
        with Vertical(id="campaign-list-panel", classes="panel surface-2") as panel:
            panel.border_title = " campaigns "
            table: DataTable[str] = DataTable(id="campaign-table", cursor_type="row", zebra_stripes=True)
            table.add_column("Campaign", key="campaign")
            table.add_column("Game System", key="game_system")
            table.add_column("Last Session", key="last_session")
            yield table

    def on_mount(self) -> None:
        self._reload_campaigns()

    def on_screen_resume(self) -> None:
        self._reload_campaigns()

    def on_resize(self, event: Resize) -> None:
        self._reload_campaigns()

    def refresh_data(self) -> None:
        self._reload_campaigns()

    def _reload_campaigns(self) -> None:
        table = self.query_one("#campaign-table", DataTable)
        selected_id = self._selected_campaign_id()

        table.clear(columns=True)
        campaign_width = max(_MIN_CAMPAIGN_WIDTH, table.size.width - _GAME_SYSTEM_WIDTH - _LAST_SESSION_WIDTH - _COLUMN_PADDING_SLACK)
        table.add_column("Campaign", key="campaign", width=campaign_width)
        table.add_column("Game System", key="game_system", width=_GAME_SYSTEM_WIDTH)
        table.add_column("Last Session", key="last_session", width=_LAST_SESSION_WIDTH)

        last_session_dates = self.application.last_session_dates()
        restored_row: int | None = None
        for index, campaign in enumerate(self.application.list_campaigns()):
            table.add_row(*self._row_cells(campaign, last_session_dates), height=2, key=str(campaign.id))
            if selected_id is not None and campaign.id == selected_id:
                restored_row = index

        if restored_row is not None:
            table.move_cursor(row=restored_row)
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in {"open_campaign", "delete_campaign", "export_campaign"}:
            return True if self._selected_campaign_id() is not None else None
        return True

    def _row_cells(self, campaign: Campaign, last_session_dates: dict[uuid.UUID, date]) -> tuple[Text, str, str]:
        description = campaign.description or ""
        campaign_cell = Text(f"{campaign.name}\n{description}", overflow="ellipsis", no_wrap=True)
        last_session = last_session_dates.get(campaign.id)
        return campaign_cell, campaign.game_system or "", str(last_session) if last_session else ""

    def _selected_campaign_id(self) -> uuid.UUID | None:
        table = self.query_one("#campaign-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return uuid.UUID(row_key) if row_key else None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_open_campaign()

    def action_new_campaign(self) -> None:
        async def on_submit(name: str, description: str | None, game_system: str | None) -> str | None:
            proceed = await self.resolve_folder_collision(
                title="Campaign Folder Exists",
                prompt=(
                    f"A campaign folder named '{name}' already exists on disk. "
                    "This may be left over from a previously deleted campaign. Delete it and continue?"
                ),
                exists=lambda: self.application.campaign_folder_exists(name),
                delete_existing=lambda: self.application.delete_orphan_campaign_folder(name),
            )
            if not proceed:
                return f"Creation cancelled: a campaign folder named '{name}' already exists."
            try:
                self.application.create_campaign(Campaign(name=name, description=description, game_system=game_system))
            except ValueError as exc:
                return str(exc)
            self._reload_campaigns()
            return None

        self.app.push_screen(CampaignDialog(title="New Campaign", submit_label="Create Campaign", on_submit=on_submit))

    def action_open_campaign(self) -> None:
        campaign_id = self._selected_campaign_id()
        if campaign_id is None:
            return
        self.app.push_screen(CampaignDetailScreen(campaign_id))

    def action_delete_campaign(self) -> None:
        campaign_id = self._selected_campaign_id()
        if campaign_id is None:
            return

        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            self.application.delete_campaign(campaign_id)
            self._reload_campaigns()

        self.app.push_screen(
            ConfirmationDialog(
                title="Delete Campaign",
                prompt="Delete this campaign? This does not remove its files on disk.",
            ),
            on_dismiss,
        )

    def action_cleanup_campaigns(self) -> None:
        def on_dismiss(confirmed: bool | None) -> None:
            if not confirmed:
                return
            removed = self.application.cleanup_orphan_campaign_dirs()
            if removed:
                self.notify(f"Removed {len(removed)} orphan campaign folder(s): {', '.join(removed)}.")
            else:
                self.notify("No orphan campaign folders found.")

        self.app.push_screen(
            ConfirmationDialog(
                title="Clean Up Campaigns",
                prompt="Remove campaign folders on disk that have no matching campaign in the database?",
            ),
            on_dismiss,
        )

    def action_export_campaign(self) -> None:
        campaign_id = self._selected_campaign_id()
        if campaign_id is None:
            return

        def is_busy() -> bool:
            sessions = self.application.list_sessions(campaign_id)
            session_ids = {session.id for session in sessions}
            return any(session.status == "processing" for session in sessions) or any(
                worker.is_running
                and (getattr(worker.node, "_campaign_id", None) == campaign_id or getattr(worker.node, "_session_id", None) in session_ids)
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
                work=lambda: self.application.export_campaign(campaign_id, destination),
                on_success=lambda _: self.notify(f"Exported campaign to {destination}."),
            )

        self.app.push_screen(
            FileSave(title="Export Campaign", location=Path.home(), default_file="campaign.zip"),
            on_picked,
        )

    def action_import_campaign(self) -> None:
        def on_picked(source: Path | None) -> None:
            if source is None:
                return

            def on_success(campaign_id: uuid.UUID) -> None:
                self._reload_campaigns()
                self.notify("Campaign imported.")

            def on_error(exc: BaseException) -> None:
                self.app.push_screen(PlayerArchiveErrorsDialog(str(exc), title="Import Campaign Failed"))

            self.run_with_progress(
                title="Import Campaign",
                message="Importing campaign database records and files…",
                work=lambda: self.application.import_campaign(source),
                on_success=on_success,
                on_error=on_error,
            )

        self.app.push_screen(
            FileOpen(
                title="Import Campaign", location=Path.home(), filters=Filters(("ZIP archives", lambda path: path.suffix.lower() == ".zip"))
            ),
            on_picked,
        )
