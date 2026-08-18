from __future__ import annotations

from rich.text import Text
from tablesage_model.model import Campaign
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable

from .base import TableSageScreen


class CampaignListScreen(TableSageScreen):
    """Shown when at least one campaign exists."""

    section = "campaigns"
    BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc"),
        Binding("n,N", "new_campaign", "New campaign", key_display="N"),
        Binding("o,O", "open_campaign", "Open campaign", key_display="O"),
        Binding("d,D", "delete_campaign", "Delete campaign", key_display="D"),
        Binding("c,C", "cleanup_campaigns", "Clean up", key_display="C"),
    ]

    def compose_content(self) -> ComposeResult:
        with Vertical(id="campaign-list-panel", classes="panel surface-2") as panel:
            panel.border_title = " campaigns "
            table: DataTable[str] = DataTable(id="campaign-table", cursor_type="row", zebra_stripes=True)
            table.add_column("Campaign", key="campaign")
            table.add_column("Game System", key="game_system")
            table.add_column("First Session", key="first_session")
            yield table

    def on_mount(self) -> None:
        self._reload_campaigns()

    def _reload_campaigns(self) -> None:
        table = self.query_one("#campaign-table", DataTable)
        table.clear()
        for campaign in self.application.list_campaigns():
            table.add_row(*self._row_cells(campaign), height=2, key=str(campaign.id))

    def _row_cells(self, campaign: Campaign) -> tuple[Text, str, str]:
        description = campaign.description or ""
        campaign_cell = Text(f"{campaign.name}\n{description}", overflow="ellipsis", no_wrap=True)
        return campaign_cell, campaign.game_system or "", ""

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_open_campaign()

    def action_new_campaign(self) -> None:
        self.notify("Creating a new campaign is coming soon.")

    def action_open_campaign(self) -> None:
        self.notify("Opening a campaign is coming soon.")

    def action_delete_campaign(self) -> None:
        self.notify("Deleting a campaign is coming soon.")

    def action_cleanup_campaigns(self) -> None:
        self.notify("Cleaning up campaigns is coming soon.")
