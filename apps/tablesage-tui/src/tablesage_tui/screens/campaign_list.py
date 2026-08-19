from __future__ import annotations

import uuid
from datetime import date

from rich.text import Text
from tablesage_model.model import Campaign
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Resize
from textual.widgets import DataTable

from ..dialogs import ConfirmationDialog, TextInputDialog
from .base import TableSageScreen
from .campaign_detail import CampaignDetailScreen

_GAME_SYSTEM_WIDTH = 20
_LAST_SESSION_WIDTH = 14
_MIN_CAMPAIGN_WIDTH = 20
_COLUMN_PADDING_SLACK = 8


class CampaignListScreen(TableSageScreen):
    """Shown when at least one campaign exists."""

    section = "campaigns"
    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc", show=False),
        Binding("n,N", "new_campaign", "New Campaign", key_display="N"),
        Binding("enter,e,E", "open_campaign", "Edit Campaign", key_display="E"),
        Binding("d,D,delete,backspace", "delete_campaign", "Delete", key_display="D"),
        Binding("c,C", "cleanup_campaigns", "Clean Up", key_display="C"),
        Binding("i,I", "import_campaign", "Import", key_display="I"),
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
        def on_dismiss(name: str | None) -> None:
            if not name:
                return
            try:
                self.application.create_campaign(Campaign(name=name))
            except ValueError as exc:
                self.notify(str(exc), severity="error")
                return
            self._reload_campaigns()

        self.app.push_screen(
            TextInputDialog(
                title="New Campaign",
                prompt="Enter a campaign name",
                placeholder="Campaign name",
                submit_label="Create Campaign",
            ),
            on_dismiss,
        )

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

    def action_import_campaign(self) -> None:
        self.notify("Importing a campaign is coming soon.")
