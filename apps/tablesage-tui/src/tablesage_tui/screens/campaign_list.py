from __future__ import annotations

import uuid
from datetime import date

from rich.text import Text
from tablesage_model.model import Campaign
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable

from ..dialogs import ConfirmationDialog, TextInputDialog
from .base import TableSageScreen


class CampaignListScreen(TableSageScreen):
    """Shown when at least one campaign exists."""

    section = "campaigns"
    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc"),
        Binding("n,N", "new_campaign", "New campaign", key_display="N"),
        Binding("enter,e,E", "open_campaign", "Open campaign", key_display="E"),
        Binding("d,D,delete,backspace", "delete_campaign", "Delete", key_display="D"),
        Binding("c,C", "cleanup_campaigns", "Clean up", key_display="C"),
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

    def _reload_campaigns(self) -> None:
        table = self.query_one("#campaign-table", DataTable)
        table.clear()
        last_session_dates = self.application.last_session_dates()
        for campaign in self.application.list_campaigns():
            table.add_row(*self._row_cells(campaign, last_session_dates), height=2, key=str(campaign.id))

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

    @work
    async def action_new_campaign(self) -> None:
        name = await self.app.push_screen_wait(
            TextInputDialog(
                title="New Campaign",
                prompt="Enter a campaign name",
                placeholder="Campaign name",
                submit_label="Create Campaign",
            )
        )
        if not name:
            return

        try:
            self.application.create_campaign(Campaign(name=name))
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return

        self._reload_campaigns()

    def action_open_campaign(self) -> None:
        self.notify("Opening a campaign is coming soon.")

    @work
    async def action_delete_campaign(self) -> None:
        campaign_id = self._selected_campaign_id()
        if campaign_id is None:
            return

        confirmed = await self.app.push_screen_wait(
            ConfirmationDialog(
                title="Delete Campaign",
                prompt="Delete this campaign? This does not remove its files on disk.",
            )
        )
        if not confirmed:
            return

        self.application.delete_campaign(campaign_id)
        self._reload_campaigns()

    @work
    async def action_cleanup_campaigns(self) -> None:
        confirmed = await self.app.push_screen_wait(
            ConfirmationDialog(
                title="Clean Up Campaigns",
                prompt="Remove campaign folders on disk that have no matching campaign in the database?",
            )
        )
        if not confirmed:
            return

        removed = self.application.cleanup_orphan_campaign_dirs()
        if removed:
            self.notify(f"Removed {len(removed)} orphan campaign folder(s): {', '.join(removed)}.")
        else:
            self.notify("No orphan campaign folders found.")

    def action_import_campaign(self) -> None:
        self.notify("Importing a campaign is coming soon.")
