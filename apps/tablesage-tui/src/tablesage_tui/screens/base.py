from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer

from ..widgets.tablesage_header import TableSageHeader


class TableSageScreen(Screen[None]):
    """Shared chrome for full-page TableSage screens."""

    section = ""
    campaign = "no campaign loaded"

    def compose(self) -> ComposeResult:
        with Vertical(classes="app-frame surface-1"):
            yield TableSageHeader(
                section=self.section,
                campaign=self.campaign,
            )

            with Vertical(classes="screen-body"):
                yield from self.compose_content()

            yield Footer()

    def compose_content(self) -> ComposeResult:
        """Supply the content unique to a particular screen."""
        yield from ()
