from __future__ import annotations

from textual.containers import Horizontal
from textual.widgets import Button


class EqualWidthButtonRow(Horizontal):
    """A Horizontal whose Button descendants share the widest button's width."""

    def on_mount(self) -> None:
        self.call_after_refresh(self._equalize_button_widths)

    def _equalize_button_widths(self) -> None:
        buttons = list(self.query(Button))
        widest_width = max((button.region.width for button in buttons), default=0)
        for button in buttons:
            button.styles.width = widest_width
