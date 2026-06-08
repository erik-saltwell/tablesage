from tablesage_model.io import load_player, load_player_set, load_session, load_session_set
from tablesage_model.model import Campaign, GlossaryEntry, Player, Session
from textual import on
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.widgets import Input, Static, TabbedContent, TabPane

from tablesage_tui.widgets import CampaignStateWidget, EmptyWidget

from .base_screen import BaseScreen, ComposeResult

EMPTY_DATE = "—"


class CampaignDetailScreen(BaseScreen):
    BINDINGS = [
        Binding("escape", "back", "Back", key_display="Esc"),
    ]

    def __init__(self, campaign: Campaign) -> None:
        super().__init__()
        self.campaign = campaign

    def get_header_section(self) -> str:
        return f"campaigns / {self.campaign.name}"

    def _sessions(self, session_count: int = -1) -> list[Session]:
        session_names = sorted(
            load_session_set(self.campaign.slug).sessions,
            key=lambda session_name: session_name.session_date,
            reverse=True,
        )
        if session_count >= 0:
            session_names = session_names[:session_count]
        return [load_session(self.campaign.slug, session_name.slug) for session_name in session_names]

    def _players(self, player_count: int = -1) -> list[Player]:
        player_names = list(load_player_set(self.campaign.slug).players)
        if player_count >= 0:
            player_names = player_names[:player_count]
        return [load_player(self.campaign.slug, player_name.slug) for player_name in player_names]

    def _glossary_entries(self, entry_count: int = -1) -> list[GlossaryEntry]:
        entries = list(self.campaign.glossary)
        if entry_count >= 0:
            return entries[:entry_count]
        return entries

    def _last_session(self) -> Session | None:
        sessions = self._sessions(session_count=1)
        if not sessions:
            return None
        return sessions[0]

    def _last_session_date_text(self) -> str:
        last_session = self._last_session()
        if last_session is None:
            return EMPTY_DATE
        return last_session.session_date.strftime("%a %b %-d %Y")

    def compose_content(self) -> ComposeResult:
        with Vertical(id="content-panel"):
            with Horizontal(id="campaign-header"):
                yield Static(id="back-keycap", classes="keycap", content="←")
                yield Static(classes="campaigns-text", content=" return to campaigns")
                yield EmptyWidget(classes="fill-space-horizontal")
            yield Static(id="campaign-name", content=self.campaign.name.upper())
            with TabbedContent(initial="overview", id="campaign-tabs"):
                with TabPane(" overview ", id="overview"):
                    with Horizontal(id="overview-tabbed-panel") as h:
                        h.border_title = "campaign details"
                        with Vertical(id="metadata-editor"):
                            yield Static(content="Description")
                            yield Input(id="description-input", placeholder="campaign description")
                            with Horizontal(id="details-row"):
                                yield Static(classes="label", content="System:")
                                yield Input(id="input-system", placeholder="system")
                                yield Static(classes="label", content="GM:")
                                yield Input(id="input-gm", placeholder="game master")
                                yield Static(classes="label", content="State: ")
                                yield CampaignStateWidget(self.campaign.state, id="campaign-state")
                        with Vertical(id="last_session_data"):
                            yield Static(content="Last Session")
                            yield Static(id="last-session-display", content=self._last_session_date_text())
                with TabPane(" sessions ", id="sessions"):
                    yield Static()

    @on(Click, "#back-keycap")
    def _on_back_click(self) -> None:
        self.action_back()

    def action_back(self) -> None:
        self.app.pop_screen()
