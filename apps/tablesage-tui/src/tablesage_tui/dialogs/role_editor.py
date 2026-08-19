from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input


class RoleEditorDialog(ModalScreen[list[str] | None]):
    """Add, edit, or remove an attendee's free-form roles as one list."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, player_name: str, roles: list[str]) -> None:
        super().__init__()
        self._player_name = player_name
        self._roles = list(roles)

    def compose(self) -> ComposeResult:
        with Vertical(id="role-editor-dialog") as dialog:
            dialog.border_title = f"Roles — {self._player_name}"
            table: DataTable[str] = DataTable(id="role-editor-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_column("Role", key="role")
            yield table
            with Horizontal(id="role-editor-add-row"):
                yield Input(id="role-editor-input", placeholder="Add a role and press Enter")
                yield Button("Remove Selected", id="role-editor-remove")
            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="role-editor-cancel")
                yield Button("Save", id="role-editor-save", variant="primary")

    def on_mount(self) -> None:
        self._reload_table()
        self.query_one("#role-editor-input", Input).focus()

    def _reload_table(self) -> None:
        table = self.query_one("#role-editor-table", DataTable)
        table.clear()
        for role in self._roles:
            table.add_row(role, key=role)

    def _add_role(self) -> None:
        input_widget = self.query_one("#role-editor-input", Input)
        name = input_widget.value.strip()
        input_widget.value = ""
        if not name or name in self._roles:
            return
        self._roles.append(name)
        self._reload_table()

    def _remove_selected(self) -> None:
        table = self.query_one("#role-editor-table", DataTable)
        if table.row_count == 0:
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        if row_key is not None and row_key in self._roles:
            self._roles.remove(row_key)
        self._reload_table()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._add_role()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "role-editor-remove":
            self._remove_selected()
        elif event.button.id == "role-editor-cancel":
            self.dismiss(None)
        elif event.button.id == "role-editor-save":
            self.dismiss(list(self._roles))

    def action_cancel(self) -> None:
        self.dismiss(None)
