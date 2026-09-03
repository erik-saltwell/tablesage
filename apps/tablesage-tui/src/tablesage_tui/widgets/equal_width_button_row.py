from __future__ import annotations

from textual.containers import Horizontal
from textual.geometry import Size
from textual.widgets import Button


class EqualWidthButtonRow(Horizontal):
    """A Horizontal whose Button descendants share the widest button's width."""

    def on_mount(self) -> None:
        self._equalize_button_widths()

    def _equalize_button_widths(self) -> None:
        # Measured via `get_content_width` (intrinsic label width, ignoring its arguments) rather
        # than `region.width`: a button inside a container still `display: none` at this point
        # (e.g. one of Manual Review's two phase panels, shown later by toggling `display`) has
        # never been laid out, so `region.width` would read 0 regardless of its label -- and
        # `min-width: 8` would then floor every button in the row to the same too-small width,
        # clipping longer labels like "Apply & Continue".
        buttons = list(self.query(Button))
        widest_width = max((button.get_content_width(Size(0, 0), Size(0, 0)) for button in buttons), default=0)
        for button in buttons:
            button.styles.width = widest_width
