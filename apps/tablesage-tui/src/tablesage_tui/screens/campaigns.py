from datetime import date
from pathlib import Path

from tablesage_model.model import CampaignState, CampaignSummary
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.widgets import DataTable, Input, Static
from textual.widgets._data_table import ColumnKey

from ..widgets import AsciiArt, EmptyWidget, FilterOption
from .base_screen import BaseScreen

LOGO_PATH: Path = Path("sun_3_small.txt")

# Shown wherever a campaign has no session history yet (no first/last session date).
EMPTY_DATE: str = "—"
CAMPAIGN_FILTERS: tuple[str, ...] = ("active", "archived", "all")
CAMPAIGN_COLUMN_NAME = "Campaign"
CAMPAIGN_COLUMN_KEY = "campaign"

CAMPAIGN_COLUMNS: tuple[str, ...] = (
    "SYSTEM       ",
    "GM           ",
    "FIRST SESSION",
    "LAST SESSION ",
    "SESSIONS     ",
    "PLAYERS      ",
)


def _format_date(value: date | None) -> str:
    return value.isoformat() if value is not None else EMPTY_DATE


class CampaignsScreen(BaseScreen):
    header_section = "campaigns"
    active_filter: str = "active"
    BINDINGS = [
        Binding("n,N", "new_campaign", "New campaign", key_display="N"),
        Binding("i,I", "import_campaign", "Import", key_display="I"),
        Binding("?", "show_help", "Help", key_display="?"),
    ]

    def __init__(self, campaigns: tuple[CampaignSummary, ...]) -> None:
        super().__init__()
        self.campaigns = campaigns
        self._campaign_name_column_key: ColumnKey | None = None
        self._campaign_column_keys: dict[str, ColumnKey] = {}

    def compose_content(self) -> ComposeResult:
        """Override in subclasses."""
        with Center(id="main-content"):
            with Vertical(id="content-panel") as content_panel:
                content_panel.border_title = "- campaigns -"
                with Horizontal(id="campaign-filter"):
                    yield AsciiArt.from_resource(LOGO_PATH, id="logo")
                    filter_counts = self._filter_counts()
                    for filter_name in CAMPAIGN_FILTERS:
                        yield FilterOption(
                            filter_name, filter_counts[filter_name], selected=filter_name == self.active_filter, classes="filter-option"
                        )
                    yield EmptyWidget(classes="fill-space-horizontal")
                    yield Input(id="search", placeholder="/search campaigns...")

                yield DataTable(id="campaign-table", cell_padding=1, cursor_type="row")

                with Horizontal(id="panel-footer"):
                    yield Static(content="> press ")
                    yield Static(classes="keycap", content="⏎")
                    yield Static(" to select")
                    yield EmptyWidget(classes="fill-space-horizontal")
                    yield Static(content="or ")
                    yield Static(classes="keycap", content="N")
                    yield Static(content=" to start a new campaign")

    def _filter_counts(self) -> dict[str, int]:
        return {
            "active": len([campaign for campaign in self.campaigns if campaign.state == CampaignState.Active]),
            "archived": len([campaign for campaign in self.campaigns if campaign.state == CampaignState.Active]),
            "all": len(self.campaigns),
        }

    def on_filter_option_selected(self, event: FilterOption.Selected) -> None:
        self.active_filter = event.filter_name
        for option in self.query(FilterOption):
            option.selected = option.filter_name == self.active_filter

    def on_mount(self) -> None:
        super().on_mount()
        table = self.query_one("#campaign-table", DataTable)

        self._campaign_name_column_key = table.add_column(
            label=CAMPAIGN_COLUMN_NAME, width=len(CAMPAIGN_COLUMN_NAME), key=CAMPAIGN_COLUMN_KEY
        )
        for column in CAMPAIGN_COLUMNS:
            self._campaign_column_keys[column] = table.add_column(label=column, width=len(column), key=column)

        for campaign in self.campaigns:
            table.add_row(
                campaign.name,
                campaign.system or EMPTY_DATE,
                campaign.default_gm or EMPTY_DATE,
                _format_date(campaign.first_session_date),
                _format_date(campaign.last_session_date),
                str(campaign.session_count),
                str(campaign.player_count),
            )

        self.call_after_refresh(self._resize_campaign_columns)

    def on_resize(self, _: events.Resize) -> None:
        self.call_after_refresh(self._resize_campaign_columns)

    def _campaign_name_column_width(self, table: DataTable) -> int:
        table_width = table.content_size.width or table.size.width
        standard_columns_width = sum(len(column) + (table.cell_padding * 2) for column in CAMPAIGN_COLUMNS)
        campaign_column_padding = table.cell_padding * 2
        available_for_name = table_width - standard_columns_width - campaign_column_padding
        return max(len(CAMPAIGN_COLUMN_NAME), available_for_name)

    def _resize_campaign_columns(self) -> None:
        try:
            table = self.query_one("#campaign-table", DataTable)
        except NoMatches:
            return

        if self._campaign_name_column_key is None or self._campaign_name_column_key not in table.columns:
            return

        table.columns[self._campaign_name_column_key].width = self._campaign_name_column_width(table)
        for column, column_key in self._campaign_column_keys.items():
            table.columns[column_key].width = len(column)

        table._require_update_dimensions = True
        table._update_count += 1
        table.check_idle()
        table.refresh()
