from tablesage_model.model import CampaignSet
from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.widgets import Static

from .base_screen import BaseScreen


class CampaignsScreen(BaseScreen):
    header_section = "campaigns"

    def __init__(self, campaigns: CampaignSet) -> None:
        self.campaigns = campaigns

    def compose_content(self) -> ComposeResult:
        """Override in subclasses."""
        with Center(id="main-content"):
            with Vertical(id="content-panel") as content_panel:
                content_panel.border_title = "- campaigns -"
                with Horizontal(id="campaign-filter"):
                    yield Static()
