from datetime import date
from pathlib import Path

from tablesage_model.model import CampaignState, CampaignSummary
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.widgets import DataTable, Input, Static

from ..widgets import AsciiArt, EmptyWidget, FilterOption
from .base_screen import BaseScreen

LOGO_PATH: Path = Path("sun_3_small.txt")

# Shown wherever a campaign has no session history yet (no first/last session date).
EMPTY_DATE: str = "—"
CAMPAIGN_FILTERS: tuple[str, ...] = ("active", "archived", "all")


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

                yield DataTable(id="campaign-table")

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
        table.add_columns(
            "Name",
            "System",
            "GM",
            "First Session",
            "Last Session",
            "Sessions",
            "Players",
            "Description",
        )
        for campaign in self.campaigns:
            table.add_row(
                campaign.name,
                campaign.system or EMPTY_DATE,
                campaign.default_gm or EMPTY_DATE,
                _format_date(campaign.first_session_date),
                _format_date(campaign.last_session_date),
                str(campaign.session_count),
                str(campaign.player_count),
                campaign.description,
            )
