from __future__ import annotations

from pathlib import Path
from typing import Literal

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Static

PickerMode = Literal["directory", "file"]

_UP_KEY = ".."


class FilesystemPickerDialog(ModalScreen[Path | None]):
    """Browse the filesystem and pick a single directory or a single file.

    Generic and validation-free by design: it has no idea what the caller
    needs the path for (e.g. that a directory must contain `.wav` files) --
    that's the caller's job. See `.documentation/import_player_from_filesystem.md`.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, title: str, mode: PickerMode, start: Path | None = None) -> None:
        super().__init__()
        self._title = title
        self._mode = mode
        self._current_dir = (start or Path.home()).resolve()

    def compose(self) -> ComposeResult:
        with Vertical(id="filesystem-picker-dialog") as dialog:
            dialog.border_title = self._title
            yield Static(str(self._current_dir), id="filesystem-picker-path")
            table: DataTable[str] = DataTable(
                id="filesystem-picker-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
            )
            table.add_column("Name", key="name")
            yield table
            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="filesystem-picker-cancel")
                if self._mode == "directory":
                    yield Button("Select This Directory", id="filesystem-picker-select-dir", variant="primary")

    def on_mount(self) -> None:
        self._reload_entries()
        self.query_one("#filesystem-picker-table", DataTable).focus()

    def _reload_entries(self) -> None:
        table = self.query_one("#filesystem-picker-table", DataTable)
        table.clear()
        self.query_one("#filesystem-picker-path", Static).update(str(self._current_dir))

        if self._current_dir.parent != self._current_dir:
            table.add_row("../", key=_UP_KEY)

        try:
            entries = sorted(self._current_dir.iterdir(), key=lambda entry: (not entry.is_dir(), entry.name.lower()))
        except OSError as exc:
            self.notify(f"Couldn't read directory: {exc}", severity="error")
            entries = []

        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                table.add_row(f"{entry.name}/", key=str(entry))
            elif self._mode == "file":
                table.add_row(entry.name, key=str(entry))

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        key = event.row_key.value
        if key is None:
            return

        if key == _UP_KEY:
            self._current_dir = self._current_dir.parent
            self._reload_entries()
            return

        path = Path(key)
        if path.is_dir():
            self._current_dir = path
            self._reload_entries()
            return

        if self._mode == "file":
            self.dismiss(path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "filesystem-picker-cancel":
            self.dismiss(None)
            return
        if event.button.id == "filesystem-picker-select-dir":
            self.dismiss(self._current_dir)

    def action_cancel(self) -> None:
        self.dismiss(None)
