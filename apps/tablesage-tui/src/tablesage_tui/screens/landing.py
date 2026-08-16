from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.widgets import Static

from ..widgets import AsciiArt, CommandButton, EmptyWidget
from .base import TableSageScreen


class LandingScreen(TableSageScreen):
    """Shown when there are no campaigns."""

    AUTO_FOCUS = ""
    section = "welcome"
    BINDINGS = [
        Binding("n,N", "new_campaign", "New campaign", key_display="N"),
        Binding("i,I", "import_campaign", "Import campaign", key_display="I"),
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

                with CommandButton(
                    "new_campaign",
                    id="start-campaign-command",
                    classes="call-to-action",
                ):
                    yield Static("> type ")
                    yield Static("N", id="first-campaign-key", classes="keycap")
                    yield Static(" to start your first campaign")

    def action_new_campaign(self) -> None:
        self.notify("New campaign setup is coming next.")

    def action_import_campaign(self) -> None:
        self.notify("Imprt campaign is coming soon.")
