from datetime import date
from pathlib import Path
from typing import cast

from rich.text import Text
from tablesage_model.model import Campaign, CampaignState, CampaignSummary
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import DataTable, Input, Static
from textual.widgets._data_table import ColumnKey

from ..dialogs import ConfirmationDialog
from ..dialogs.new_campaign import NewCampaignDialog, NewCampaignResult
from ..viewmodel import ModelStore, ModelStoreHost
from ..widgets import AsciiArt, EmptyWidget, FilterOption
from .base_screen import BaseScreen
from .campaign_detail import CampaignDetailScreen

LOGO_PATH: Path = Path("sun_3_small.txt")

# Shown wherever a campaign has no session history yet (no first/last session date).
EMPTY_DATE: str = "—"
CAMPAIGN_FILTERS: tuple[str, ...] = ("active", "unstarted", "archived", "all")
CAMPAIGN_COLUMN_NAME = "Campaign"
CAMPAIGN_COLUMN_KEY = "campaign"
CAMPAIGN_NAME_STYLE = "bold #d6d1bf"
UNSTARTED_STATUS_STYLE = "#d8b06a"
ACTIVE_STATUS_STYLE = "#6f8a5a"
ARCHIVED_STATUS_STYLE = "#8a5a5a"

CAMPAIGN_COLUMNS: tuple[str, ...] = (
    "SYSTEM       ",
    "GM           ",
    "FIRST SESSION",
    "LAST SESSION ",
    "SESSIONS     ",
    "PLAYERS      ",
    "STATUS      ",
)


def _format_date(value: date | None) -> str:
    return value.isoformat() if value is not None else EMPTY_DATE


def _format_campaign_state(state: CampaignState) -> Text:
    if state == CampaignState.Active:
        color = ACTIVE_STATUS_STYLE
    elif state == CampaignState.Unstarted:
        color = UNSTARTED_STATUS_STYLE
    else:
        color = ARCHIVED_STATUS_STYLE
    return Text("●", style=color)


def _format_campaign_cell(campaign: CampaignSummary) -> Text:
    description = campaign.description.strip()
    cell = Text(no_wrap=True, overflow="crop")
    cell.append(campaign.name, style=CAMPAIGN_NAME_STYLE)
    cell.append("\n")
    cell.append(description)
    return cell


def _campaign_name_from_cell(cell: object) -> str:
    if isinstance(cell, Text):
        return cell.plain.splitlines()[0]
    return str(cell)


class CampaignsScreen(BaseScreen):
    header_section = "campaigns"
    active_filter: reactive[str] = reactive("active", init=False)
    search_text: reactive[str] = reactive("", init=False)
    highlighted_campaign_name: reactive[str] = reactive("", init=False)
    highlighted_campaign_slug: reactive[str] = reactive("", init=False)

    BINDINGS = [
        Binding("n,N", "new_campaign", "New campaign", key_display="N"),
        Binding("i,I", "import_campaign", "Import", key_display="I"),
        Binding("delete", "delete_campaign", "Delete Command", key_display="Del"),
        Binding("c,C", "clean_deleted_campaigns", "Clean Orphaned Campaigns", key_display="C"),
        Binding("?", "show_help", "Help", key_display="?"),
    ]

    def __init__(self, campaigns: tuple[CampaignSummary, ...]) -> None:
        super().__init__()
        self.campaigns = campaigns
        self._campaign_name_column_key: ColumnKey | None = None
        self._campaign_column_keys: dict[str, ColumnKey] = {}

    def _filtered_campaigns(self) -> tuple[CampaignSummary, ...]:
        campaigns = self.campaigns

        if self.active_filter == "unstarted":
            campaigns = tuple(c for c in campaigns if c.state == CampaignState.Unstarted)
        elif self.active_filter == "active":
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

        filtered_campaigns = self._filtered_campaigns()
        table.clear()
        for campaign in filtered_campaigns:
            table.add_row(
                _format_campaign_cell(campaign),
                campaign.system or EMPTY_DATE,
                campaign.default_gm or EMPTY_DATE,
                _format_date(campaign.first_session_date),
                _format_date(campaign.last_session_date),
                str(campaign.session_count),
                str(campaign.player_count),
                _format_campaign_state(campaign.state),
                height=2,
                key=campaign.slug,
            )

        self.highlighted_campaign_name = filtered_campaigns[0].name if filtered_campaigns else ""
        self.highlighted_campaign_slug = filtered_campaigns[0].slug if filtered_campaigns else ""
        self.refresh_bindings()

    @property
    def store(self) -> ModelStore:
        host = cast(ModelStoreHost, self.app)
        return host.store

    def _open_campaign(self) -> None:
        campaign = self._highlighted_campaign()
        if campaign is None:
            return
        self.app.push_screen(CampaignDetailScreen(campaign))

    def _highlighted_campaign(self) -> Campaign | None:
        if not self.highlighted_campaign_slug:
            return None
        return self.store.load_campaign(self.highlighted_campaign_slug)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "delete_campaign":
            return bool(self.highlighted_campaign_slug)

        return super().check_action(action, parameters)

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
                            filter_name,
                            filter_counts[filter_name],
                            selected=filter_name == self.active_filter,
                            classes=f"filter-option filter-{filter_name}",
                        )
                    yield EmptyWidget(classes="fill-space-horizontal")
                    yield Input(id="search", placeholder="/search campaigns...")

                yield DataTable(id="campaign-table", cell_padding=1, cursor_type="row")

                with Horizontal(id="panel-footer"):
                    yield Static(content="> press ", classes="selection-footer")
                    yield Static(classes="keycap selection-footer", content="⏎")
                    yield Static(" to select ", classes="selection-footer")
                    yield Static(content="", id="highlighted-campaign-name", classes="selection-footer")
                    yield EmptyWidget(classes="fill-space-horizontal")
                    yield Static(content="or ")
                    yield Static(classes="keycap", content="N")
                    yield Static(content=" to start a new campaign")

    def _filter_counts(self) -> dict[str, int]:
        return {
            "unstarted": len([c for c in self.campaigns if c.state == CampaignState.Unstarted]),
            "active": len([c for c in self.campaigns if c.state == CampaignState.Active]),
            "archived": len([c for c in self.campaigns if c.state == CampaignState.Archived]),
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

        campaign_name = event.data_table.get_cell(event.row_key, self._campaign_name_column_key)
        self.highlighted_campaign_name = _campaign_name_from_cell(campaign_name)
        self.highlighted_campaign_slug = str(event.row_key.value)
        self.refresh_bindings()
        self._open_campaign()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if self._campaign_name_column_key is None:
            return

        campaign_name = event.data_table.get_cell(event.row_key, self._campaign_name_column_key)
        self.highlighted_campaign_name = _campaign_name_from_cell(campaign_name)
        self.highlighted_campaign_slug = str(event.row_key.value)
        self.refresh_bindings()

    def watch_highlighted_campaign_name(self, campaign_name: str) -> None:
        for widget in self.query("#panel-footer .selection-footer"):
            widget.display = bool(campaign_name)

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

    def action_new_campaign(self) -> None:
        existing_slugs = frozenset(c.slug for c in self.store.load_campaigns())
        self.app.push_screen(NewCampaignDialog(existing_slugs=existing_slugs), self._on_new_campaign)

    def _on_new_campaign(self, result: NewCampaignResult | None) -> None:
        if result and result.name:
            self.store.create_campaign(
                campaign_name=result.name,
                description=result.description,
                default_gm=result.default_gm,
                system=result.system,
            )
            campaigns = self.store.load_campaigns()
            self.app.switch_screen(CampaignsScreen(campaigns))

    def action_delete_campaign(self) -> None:
        campaign_slug = self.highlighted_campaign_slug
        if not campaign_slug:
            self.notify("Select a campaign to delete.")
            return

        self.app.push_screen(
            ConfirmationDialog(
                title="Confirm Campaign Deletion",
                prompt=(
                    f"Do you want to remove {self.highlighted_campaign_name} from the system?  You will need to run the "
                    '"clean orphaned campaigns" command to remove it from disk?'
                ),
                show_cancel=False,
            ),
            lambda confirmed: self._on_delete_campaign_confirmation(confirmed, campaign_slug),
        )

    def _on_delete_campaign_confirmation(self, confirmed: bool | None, campaign_slug: str) -> None:
        if not confirmed:
            return

        self.perform_delete(campaign_slug)
        self._reload_campaigns()

    def perform_delete(self, campaign_slug: str) -> None:
        self.store.delete_campaign(campaign_slug)

    def action_clean_deleted_campaigns(self) -> None:
        deleted_campaigns = self.store.list_deleted_campaigns()
        if not deleted_campaigns:
            self.notify("No deleted campaigns to remove.")
            return

        self.app.push_screen(
            ConfirmationDialog(
                title="Confirm Deleted Campaign Cleanup",
                prompt=f"Remove {len(deleted_campaigns)} deleted campaign(s) from disk?",
                show_cancel=False,
            ),
            self._on_clean_deleted_campaigns_confirmation,
        )

    def _on_clean_deleted_campaigns_confirmation(self, confirmed: bool | None) -> None:
        if not confirmed:
            return

        deleted = self.store.clean_deleted_campaigns()
        if deleted:
            self.notify(f"Removed {len(deleted)} orphaned campaign(s).")
            return

        self.notify("No deleted orphaned to remove.")

    def _reload_campaigns(self) -> None:
        self.campaigns = self.store.load_campaigns()
        self._refresh_campaign_table()
