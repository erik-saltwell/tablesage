from typing import ClassVar

from textual.app import ComposeResult
from textual.screen import CSSPathType, Screen
from textual.widgets import Footer

from ..widgets.tablesage_header import TableSageHeader

BASE_SCREEN_CSS = "../styles/base_screen.tcss"


class BaseScreen(Screen):
    CSS_PATH: ClassVar[CSSPathType | None] = [BASE_SCREEN_CSS]

    """Common shell for app screens."""

    def compose(self) -> ComposeResult:
        yield TableSageHeader()
        yield from self.compose_content()
        yield Footer()

    def compose_content(self) -> ComposeResult:
        """Override in subclasses."""
        yield
