from datetime import date
from pathlib import Path

from tablesage_model.model import CampaignState, CampaignSummary
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
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
    active_filter: reactive[str] = reactive("active", init=False)
    search_text: reactive[str] = reactive("", init=False)
    highlighted_campaign_name: reactive[str] = reactive("", init=False)

    BINDINGS = [
        Binding("n,N", "new_campaign", "New campaign", key_display="N"),
        Binding("i,I", "import_campaign", "Import", key_display="I"),
        Binding("?", "show_help", "Help", key_display="?"),
    ]

    def _filtered_campaigns(self) -> tuple[CampaignSummary, ...]:
        campaigns = self.campaigns

        if self.active_filter == "active":
            campaigns = tuple(c for c in campaigns if c.state == CampaignState.Active)
        elif self.active_filter == "archived":
            campaigns = tuple(c for c in campaigns if c.state == CampaignState.Archived)

        search_text = self.search_text.strip().lower()
        if search_text:
            campaigns = tuple(c for c in campaigns if search_text in c.name.lower())

        return campaigns

    def _refresh_campaign_table(self) -> None:
        try:
            table = self.query_one("#campaign-table", DataTable)
        except NoMatches:
            return

        if self._campaign_name_column_key is None or self._campaign_name_column_key not in table.columns:
            return

        table.clear()
        for campaign in self._filtered_campaigns():
            table.add_row(
                campaign.name,
                campaign.system or EMPTY_DATE,
                campaign.default_gm or EMPTY_DATE,
                _format_date(campaign.first_session_date),
                _format_date(campaign.last_session_date),
                str(campaign.session_count),
                str(campaign.player_count),
            )

    def __init__(self, campaigns: tuple[CampaignSummary, ...]) -> None:
        super().__init__()
        self.campaigns = campaigns
        self._campaign_name_column_key: ColumnKey | None = None
        self._campaign_column_keys: dict[str, ColumnKey] = {}

    def _open_campaign(self, campaign_name: str) -> None:
        self.notify(f"Selected {campaign_name}")

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
                    yield Static(" to select ")
                    yield Static(content="", id="highlighted-campaign-name")
                    yield EmptyWidget(classes="fill-space-horizontal")
                    yield Static(content="or ")
                    yield Static(classes="keycap", content="N")
                    yield Static(content=" to start a new campaign")

    def _filter_counts(self) -> dict[str, int]:
        return {
            "active": len([campaign for campaign in self.campaigns if campaign.state == CampaignState.Active]),
            "archived": len([campaign for campaign in self.campaigns if campaign.state == CampaignState.Archived]),
            "all": len(self.campaigns),
        }

    def _sync_filter_options(self) -> None:
        for option in self.query(FilterOption):
            option.selected = option.filter_name == self.active_filter

    def on_filter_option_selected(self, event: FilterOption.Selected) -> None:
        self.active_filter = event.filter_name
        self.search_text = ""
        self.query_one("#search", Input).value = ""

    def watch_active_filter(self, _: str) -> None:
        self._sync_filter_options()
        self._refresh_campaign_table()

    def watch_search_text(self, _: str) -> None:
        self._refresh_campaign_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if self._campaign_name_column_key is None:
            return

        campaign_name = event.data_table.get_cell(
            event.row_key,
            self._campaign_name_column_key,
        )

        self._open_campaign(str(campaign_name))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if self._campaign_name_column_key is None:
            return

        campaign_name = event.data_table.get_cell(event.row_key, self._campaign_name_column_key)
        self.highlighted_campaign_name = str(campaign_name)

    def watch_highlighted_campaign_name(self, campaign_name: str) -> None:
        self.query_one("#highlighted-campaign-name", Static).update(campaign_name)

    def on_mount(self) -> None:
        super().on_mount()
        table = self.query_one("#campaign-table", DataTable)

        self._campaign_name_column_key = table.add_column(
            label=CAMPAIGN_COLUMN_NAME, width=len(CAMPAIGN_COLUMN_NAME), key=CAMPAIGN_COLUMN_KEY
        )
        for column in CAMPAIGN_COLUMNS:
            self._campaign_column_keys[column] = table.add_column(label=column, width=len(column), key=column)

        self._refresh_campaign_table()

        self.call_after_refresh(self._resize_campaign_columns)
        self.call_after_refresh(table.focus)

    def on_resize(self, _: events.Resize) -> None:
        self.call_after_refresh(self._resize_campaign_columns)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search":
            return

        self.search_text = event.value

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
