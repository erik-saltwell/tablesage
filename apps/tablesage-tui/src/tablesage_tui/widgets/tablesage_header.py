from __future__ import annotations

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class TableSageHeader(Widget):
    version = reactive("0.3.1")
    section = reactive("welcome")
    campaign = reactive("no campaign loaded")

    def compose(self) -> ComposeResult:
        with Horizontal(classes="brand-panel"):
            yield Static("❦ TableSage", classes="brand")
            yield Static("", classes="header-context")
        with Horizontal(classes="info-panel"):
            yield Static("", classes="header-campaign")
            yield Static("", classes="clock")

    def on_mount(self) -> None:
        self.set_interval(10, self.update_clock)
        self.refresh_text()

    def refresh_text(self) -> None:
        self.query_one(".header-context", Static).update(f"v{self.version} · {self.section}")
        self.query_one(".header-campaign", Static).update(self.campaign)
        self.update_clock()

    def update_clock(self) -> None:
        self.query_one(".clock", Static).update(datetime.now().strftime("%H:%M:%S"))

    def watch_version(self) -> None:
        self.refresh_text()

    def watch_section(self) -> None:
        self.refresh_text()

    def watch_campaign(self) -> None:
        self.refresh_text()
