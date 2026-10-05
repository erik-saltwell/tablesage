from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from textual import events
from textual.coordinate import Coordinate
from textual.message import Message
from textual.widgets import DataTable

from ..audio_playback import PlaybackMode, ReviewPlayback


class VoiceClipTable(DataTable[object]):
    """Shared row-driven clip playback for Player Detail and Review Samples."""

    class PlaybackChanged(Message):
        pass

    def __init__(self, *, id: str, clip_path: Callable[[str], Path]) -> None:
        super().__init__(id=id, cursor_type="row", zebra_stripes=True, classes="tablesage-table")
        self._clip_path = clip_path
        self._durations: dict[str, float] = {}
        self._playing_key: str | None = None
        self._auto_key: str | None = None
        self._playback = ReviewPlayback(self, on_advance=self.advance, on_mode_changed=self._mode_changed)

    @property
    def mode_label(self) -> str:
        return "Autoplay" if self._playback.mode is PlaybackMode.AUTO else "Manual"

    @property
    def selected_filename(self) -> str | None:
        if not self.row_count:
            return None
        return self.coordinate_to_cell_key(self.cursor_coordinate).row_key.value

    def add_clip(self, filename: str, duration: float, *cells: object) -> None:
        self._durations[filename] = duration
        self.add_row(*cells, key=filename)

    def reset_clips(self) -> None:
        self.stop_playback()
        self._durations.clear()
        self.clear()

    def _mode_changed(self) -> None:
        self.post_message(self.PlaybackChanged())

    def play_selected(self) -> None:
        filename = self.selected_filename
        if filename is None:
            return
        self._playing_key = filename
        try:
            self._playback.play(self._clip_path(filename), self._durations[filename])
        except (OSError, ValueError) as exc:
            self.stop_playback()
            self.notify(f"Could not play '{filename}': {exc}", severity="error", markup=False)

    def toggle_mode(self) -> None:
        if self.selected_filename is None:
            return
        if self._playing_key is None:
            self.play_selected()
        self._playback.toggle_mode()

    def stop_playback(self) -> None:
        self._playback.stop()
        self._playback.set_manual()
        self._playing_key = None
        self._auto_key = None

    def advance(self) -> bool:
        if self.cursor_row + 1 >= self.row_count:
            return False
        row = self.cursor_row + 1
        self._auto_key = self.coordinate_to_cell_key(Coordinate(row, 0)).row_key.value
        self.move_cursor(row=row)
        return True

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table is not self:
            return
        filename = event.row_key.value
        automatic = filename == self._auto_key
        self._auto_key = None
        if (not self.has_focus and not automatic) or filename == self._playing_key:
            return
        if not automatic:
            self._playback.set_manual()
        self.play_selected()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table is self:
            event.stop()
            self._playback.set_manual()
            self.play_selected()

    def on_click(self, event: events.Click) -> None:
        # Clicking anywhere in the selected row should replay, not merely change columns.
        meta = event.style.meta
        if meta.get("row", -1) == self.cursor_row and "column" in meta:
            self.cursor_coordinate = Coordinate(self.cursor_row, meta["column"])

    def on_unmount(self) -> None:
        self.stop_playback()
