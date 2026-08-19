from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.widgets import Static

from ..widgets import AsciiArt, CommandButton, EmptyWidget
from .base import TableSageScreen
from .campaign_list import CampaignListScreen
from .players_list import PlayersListScreen


class LandingScreen(TableSageScreen):
    """The app's permanent home/hub screen, always shown at startup."""

    AUTO_FOCUS = ""
    section = "welcome"
    BINDINGS = [
        Binding("c,C", "show_campaigns", "Campaigns", key_display="C"),
        Binding("p,P", "show_players", "Players", key_display="P"),
    ]

    def compose_content(self) -> ComposeResult:
        with Vertical(id="welcome-panel", classes="panel surface-2") as panel:
            panel.border_title = " welcome "

            with Vertical(id="welcome-content"):
                with Grid(id="welcome-lockup"):
                    yield EmptyWidget(id="logo-spacer")

                    yield AsciiArt.from_resource(
                        "acorn.txt",
                        markup=True,
                        id="welcome-logo",
                    )

                    yield AsciiArt.from_resource(
                        "table_standard.txt",
                        id="table-wordmark",
                    )

                    yield AsciiArt.from_resource(
                        "sage_computer.txt",
                        id="sage-wordmark",
                    )

                yield Static(
                    "─" * 47,
                    id="welcome-divider",
                )

                with Vertical(id="welcome-actions"):
                    with CommandButton(
                        "show_campaigns",
                        id="show-campaigns-command",
                        classes="call-to-action",
                    ):
                        yield Static("> type ")
                        yield Static("C", id="campaigns-key", classes="keycap")
                        yield Static(" to browse campaigns")

                    with CommandButton(
                        "show_players",
                        id="show-players-command",
                        classes="call-to-action",
                    ):
                        yield Static("> type ")
                        yield Static("P", id="players-key", classes="keycap")
                        yield Static(" to browse players")

    def action_show_campaigns(self) -> None:
        self.app.push_screen(CampaignListScreen())

    def action_show_players(self) -> None:
        self.app.push_screen(PlayersListScreen())

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "refresh_screen":
            # Landing shows no live data (base `TableSageScreen`'s F5 binding is inherited
            # regardless), so hide it rather than advertise a refresh that does nothing.
            return False
        return True
