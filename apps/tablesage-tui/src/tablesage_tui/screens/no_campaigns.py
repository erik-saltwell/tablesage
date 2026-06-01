from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Horizontal, Vertical
from textual.widgets import Static

from ..widgets.ascii_art import AsciiArt
from ..widgets.command_button import CommandButton
from .base_screen import BaseScreen
from .help import HelpScreen

TABLE_PATH: Path = Path("table_standard.txt")
SAGE_PATH: Path = Path("sage_computer.txt")
LOGO_PATH: Path = Path("sun_2.txt")


class _Empty(Container): ...


class NoCampaignsScreen(BaseScreen):
    ENABLE_COMMAND_PALETTE = False
    header_section = "welcome"
    show_footer = False
    BINDINGS = [
        Binding("n,N", "new_campaign", "New campaign", key_display="N"),
        Binding("i,I", "import_campaign", "Import", key_display="I"),
        Binding("?", "show_help", "Help", key_display="?"),
    ]

    def compose_content(self) -> ComposeResult:

        with Center(id="main-content"):
            with Center(id="splash-panel") as splash_panel:
                splash_panel.border_title = "- welcome -"

                with Vertical(id="splash-panel-content"):
                    yield AsciiArt.from_resource(LOGO_PATH, id="logo")
                    with Horizontal(classes="wordmark"):
                        yield AsciiArt.from_resource(TABLE_PATH, id="tablemark")
                        yield AsciiArt.from_resource(SAGE_PATH, id="sagemark")
                    with Horizontal(classes="subtitle"):
                        yield Static(classes="campaigns", content="campaigns.")
                        yield Static(classes="intelligent", content="intelligent.")
                    with Center():
                        yield Static(
                            classes="divider",
                            content="........................................................................................",
                        )
                    with Center():
                        with CommandButton(
                            "new_campaign",
                            id="start-campaign-command",
                            classes="call-to-action primary-cta",
                        ):
                            yield Static("> type ")
                            yield Static("N", id="first-campaign-key", classes="keycap")
                            yield Static(" to start your first campaign")
                    yield Static(classes="bottom-spacer")
                    with Center():
                        with Horizontal(classes="commmon-actions"):
                            with CommandButton(
                                "new_campaign",
                                id="new-campaign-command",
                                classes="splash-command",
                            ):
                                yield Static(classes="keycap", content="N")
                                yield Static(classes="cta-lbl", content="create new campaign")
                            with CommandButton(
                                "import_campaign",
                                id="import-campaign-command",
                                classes="splash-command",
                            ):
                                yield Static(classes="keycap", content="I")
                                yield Static(classes="cta-lbl", content="import from json/yaml")
                            with CommandButton(
                                "show_help",
                                id="help-command",
                                classes="splash-command",
                            ):
                                yield Static(classes="keycap", content="?")
                                yield Static(classes="cta-lbl cta-lbl-last", content="keybindings & help")

    def action_new_campaign(self) -> None:
        self.notify("New campaign")

    def action_import_campaign(self) -> None:
        self.notify("Import campaign")

    def action_show_help(self) -> None:
        self.app.push_screen(HelpScreen())
