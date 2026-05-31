from typing import ClassVar

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer

from ..widgets.tablesage_header import TableSageHeader


class BaseScreen(Screen):
    """Common shell for app screens."""

    header_section: ClassVar[str] = "welcome"
    show_header: ClassVar[bool] = True
    show_footer: ClassVar[bool] = True

    def compose(self) -> ComposeResult:
        if self.show_header:
            yield TableSageHeader()
        yield from self.compose_content()
        if self.show_footer:
            yield Footer()

    def compose_content(self) -> ComposeResult:
        """Override in subclasses."""
        return iter(())

    def on_mount(self) -> None:
        if self.show_header:
            self.query_one(TableSageHeader).section = self.header_section
