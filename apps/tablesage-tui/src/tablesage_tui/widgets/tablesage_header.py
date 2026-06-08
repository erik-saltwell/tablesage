from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class TableSageHeader(Widget):
    version = reactive("0.3.1")
    section = reactive("welcome")
    campaign = reactive("no campaign loaded")

    def __init__(self, section: str = "welcome", campaign: str = "no campaign loaded", version: str = "0.3.1") -> None:
        super().__init__()
        self._initial_section = section
        self._initial_campaign = campaign
        self._initial_version = version

    def compose(self) -> ComposeResult:
        with Horizontal(classes="brand-panel"):
            yield Static("❦ TableSage", classes="brand")
            yield Static("", classes="header-context")
        with Horizontal(classes="info-panel"):
            yield Static("", classes="header-campaign")
            yield Static("", classes="clock")

    def on_mount(self) -> None:
        self.set_interval(10, self.update_clock)
        self.version = self._initial_version
        self.section = self._initial_section
        self.campaign = self._initial_campaign
        self.refresh_text()

    def refresh_text(self) -> None:
        try:
            header_context = self.query_one(".header-context", Static)
            header_campaign = self.query_one(".header-campaign", Static)
        except NoMatches:
            return

        header_context.update(f"v{self.version} · {self.section}")
        header_campaign.update(self.campaign)
        self.update_clock()

    def update_clock(self) -> None:
        try:
            self.query_one(".clock", Static).update(datetime.now().strftime("%H:%M:%S"))
        except NoMatches:
            return

    def watch_version(self) -> None:
        self.refresh_text()

    def watch_section(self) -> None:
        self.refresh_text()

    def watch_campaign(self) -> None:
        self.refresh_text()
