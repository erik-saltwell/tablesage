from __future__ import annotations

from typing import Literal

from rich.text import Text
from textual.coordinate import Coordinate
from textual.widgets import DataTable

_ZERO_SAMPLE_COLOR = "#d45a4f"
_SELECTED_ZERO_SAMPLE_COLOR = "#8f2f2f"


def sample_count_cell(count: int) -> Text:
    """Render a sample count, emphasizing only an empty count."""
    return Text(str(count), style=_ZERO_SAMPLE_COLOR if count == 0 else "")


class SampleCountDataTable(DataTable[object]):
    """A table that explains its zero-valued Samples cells on hover."""

    def __init__(
        self,
        *,
        zero_sample_tooltip: str,
        id: str | None = None,
        cursor_type: Literal["cell", "row", "column", "none"] = "cell",
        cursor_foreground_priority: Literal["renderable", "css"] = "renderable",
        zebra_stripes: bool = False,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            id=id,
            cursor_type=cursor_type,
            cursor_foreground_priority=cursor_foreground_priority,
            zebra_stripes=zebra_stripes,
            classes=classes,
        )
        self._zero_sample_tooltip = zero_sample_tooltip

    def watch_hover_coordinate(self, old: Coordinate, value: Coordinate) -> None:
        super().watch_hover_coordinate(old, value)
        if not self.is_valid_coordinate(value):
            self.tooltip = None
            return
        _, column_key = self.coordinate_to_cell_key(value)
        cell = self.get_cell_at(value)
        self.tooltip = self._zero_sample_tooltip if column_key.value == "samples" and str(cell) == "0" else None

    def watch_cursor_coordinate(self, old_coordinate: Coordinate, new_coordinate: Coordinate) -> None:
        super().watch_cursor_coordinate(old_coordinate, new_coordinate)
        self._style_zero_sample(old_coordinate, selected=False)
        self._style_zero_sample(new_coordinate, selected=True)

    def _style_zero_sample(self, coordinate: Coordinate, *, selected: bool) -> None:
        if not self.is_valid_coordinate(coordinate):
            return
        sample_cell = self.get_cell_at(Coordinate(coordinate.row, 0))
        if isinstance(sample_cell, Text) and str(sample_cell) == "0":
            sample_cell.style = _SELECTED_ZERO_SAMPLE_COLOR if selected else _ZERO_SAMPLE_COLOR
