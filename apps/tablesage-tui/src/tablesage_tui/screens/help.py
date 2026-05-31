from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from ..widgets.tablesage_header import TableSageHeader


class HelpScreen(Screen[None]):
    BINDINGS = [
        Binding("escape,?", "dismiss", "Back", key_display="Esc"),
    ]

    def compose(self) -> ComposeResult:
        yield TableSageHeader()

        with Center(id="help-content"):
            with Center(id="help-panel") as help_panel:
                help_panel.border_title = "- keybindings & help -"

                with Vertical(id="help-panel-content"):
                    yield Static("TableSage commands", classes="help-title")
                    yield Static(
                        "Use these keys from the home screen to start or load a campaign.",
                        classes="help-copy",
                    )

                    with Vertical(classes="help-bindings"):
                        with Horizontal(classes="help-binding-row"):
                            yield Static("N", classes="keycap help-key")
                            yield Static("Create a new campaign", classes="help-binding-description")
                        with Horizontal(classes="help-binding-row"):
                            yield Static("I", classes="keycap help-key")
                            yield Static("Import a campaign from JSON/YAML", classes="help-binding-description")
                        with Horizontal(classes="help-binding-row"):
                            yield Static("?", classes="keycap help-key")
                            yield Static("Open or close this help screen", classes="help-binding-description")
                        with Horizontal(classes="help-binding-row"):
                            yield Static("Esc", classes="keycap help-key")
                            yield Static("Return to the previous screen", classes="help-binding-description")

                    yield Static("", classes="bottom-spacer")
                    yield Static("Campaign workflows are coming next.", classes="help-note")

    def on_mount(self) -> None:
        self.query_one(TableSageHeader).section = "help"
