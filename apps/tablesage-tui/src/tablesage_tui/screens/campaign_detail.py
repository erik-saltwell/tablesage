from rich.text import Text
from tablesage_model.io import load_player, load_player_set, load_session, load_session_set
from tablesage_model.model import Campaign, CampaignState, GlossaryEntry, Player, Session
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Static

from tablesage_tui.widgets import EmptyWidget

from ..widgets.tablesage_header import TableSageHeader
from .base_screen import BaseScreen, ComposeResult

ACTIVE_STATE_STYLE = "#6f8a5a"
ARCHIVED_STATE_STYLE = "#d8b06a"
EMPTY_DATE = "—"

CAMPAIGN_DETAIL_TABS: list[str] = [
    "[ overview ]",
    "[ sessions ]",
    "[ glossary ]",
    "[ players ]",
]


class CampaignDetailScreen(BaseScreen):
    BINDINGS = [
        Binding("escape", "back", "Back", key_display="Esc"),
    ]

    def __init__(self, campaign: Campaign) -> None:
        super().__init__()
        self.campaign = campaign

    def _campaign_state(self) -> Static:
        state_text = str(self.campaign.state).lower()
        state_style = ACTIVE_STATE_STYLE if self.campaign.state == CampaignState.Active else ARCHIVED_STATE_STYLE
        content = Text()
        content.append("● ", style=state_style)
        content.append(state_text)
        return Static(id="campaign-state", content=content)

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
                yield Static(classes="keycap", content="←")
                yield Static(content=" campaigns")
                with Vertical(id="campaign-overview"):
                    with Horizontal(id="name-and-state"):
                        yield Static(id="campaign-name", content=self.campaign.name)
                        yield self._campaign_state()
                    with Horizontal(id="campaign-details"):
                        yield Static(content="system")
                        yield Input(placeholder="<system>")
                        yield Static(content="gm")
                        yield Input(placeholder="<gm>")
                yield EmptyWidget(classes="fill-space-horizontal")
                with Vertical(id="last-session-data"):
                    yield Static(classes="label", content="LAST SESSION")
                    yield Static(id="last-session-display", content=self._last_session_date_text())
        with Horizontal(
            id="campaign-tabs",
        ):
            for tab_name in CAMPAIGN_DETAIL_TABS:
                yield Static(content=tab_name)
        with Container(id="campiagn-description-container") as d:
            d.border_title = "description"
            with Input(id="campaign-description") as desc_input:
                desc_input.value = self.campaign.description
        with Horizontal(id="sessions-and-glossary"):
            with Vertical(id="sessions-summary") as s:
                s.border_title = "recent sessions"
                for session in self._sessions(3):
                    with Vertical(classes="recent-session-item"):
                        yield Static(classes="recent-session-item-date", content=session.session_date.strftime("%Y.%m.%d"))
                        yield Static(classes="recent-session-item-name", content=session.name)
                yield Static(classes="see-more-footer", content="> sessions screen")
            with Vertical(id="glossary-summary") as g:
                g.border_title = "glossary"
                for entry in self._glossary_entries():
                    with Vertical(classes="glossary-entry"):
                        yield Static(classes="glossary-entry-term", content=entry.term)
                        yield Static(classes="glossary-entry-description", content=entry.description)
                yield Static(classes="see-more-footer", content="> glossary screen")
        with Vertical(id="players-summary") as p:
            p.border_title = "players"
            with Horizontal(id="players-summary-players"):
                for player in self._players():
                    yield Static(classes="player-entry", content=player.name)
            yield Static(classes="see-more-footer", content="> players screen")

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one(TableSageHeader).section = f"campaigns / {self.campaign.name}"

    def action_back(self) -> None:
        self.app.pop_screen()
