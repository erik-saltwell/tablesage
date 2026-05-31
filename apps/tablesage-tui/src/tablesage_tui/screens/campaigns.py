from textual.app import ComposeResult
from textual.containers import Center, Container

from .base_screen import BaseScreen


class CampaignsScreen(BaseScreen):
    header_section = "campaigns"

    def compose_content(self) -> ComposeResult:
        """Override in subclasses."""
        with Center(id="main-content"):
            with Center(id="content-panel") as content_panel:
                content_panel.border_title = "- campaigns -"
                yield Container()
