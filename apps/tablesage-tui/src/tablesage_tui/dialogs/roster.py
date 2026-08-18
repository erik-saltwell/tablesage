from __future__ import annotations

import uuid

from tablesage_model.model import GAME_MASTER_ROLE, Player
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Static

from .generic import TextInputDialog


class PlayerPickerDialog(ModalScreen[uuid.UUID | None]):
    """Pick an existing player to add to a campaign roster."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, players: list[Player]) -> None:
        super().__init__()
        self._players = players

    def compose(self) -> ComposeResult:
        with Vertical(id="player-picker-dialog") as dialog:
            dialog.border_title = "Add Player"
            if not self._players:
                yield Static("No players are available to add.", id="player-picker-empty")
                with Horizontal(classes="dialog-actions"):
                    yield Button("Close", id="player-picker-close")
            else:
                table: DataTable[str] = DataTable(
                    id="player-picker-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
                )
                table.add_column("Player", key="name")
                for player in self._players:
                    table.add_row(player.name, key=str(player.id))
                yield table
                with Horizontal(classes="dialog-actions"):
                    yield Button("Cancel", id="player-picker-cancel")
                    yield Button("Select", id="player-picker-select", variant="primary")

    def on_mount(self) -> None:
        if self._players:
            self.query_one("#player-picker-table", DataTable).focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id in ("player-picker-cancel", "player-picker-close"):
            self.dismiss(None)
            return
        if event.button.id == "player-picker-select":
            self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        table = self.query_one("#player-picker-table", DataTable)
        if table.row_count == 0:
            self.dismiss(None)
            return
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        self.dismiss(uuid.UUID(row_key) if row_key else None)


class RolePickerDialog(ModalScreen[str | None]):
    """Choose "Game Master" or "Character" (with a name) for one player's default role."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, player_name: str, current_role: str | None = None) -> None:
        super().__init__()
        self._player_name = player_name
        self._current_role = current_role

    def compose(self) -> ComposeResult:
        with Vertical(id="role-picker-dialog") as dialog:
            dialog.border_title = f"Default Role — {self._player_name}"
            yield Static(
                f"Is {self._player_name} the Game Master, or do they play a character?",
                id="role-picker-prompt",
            )
            if self._current_role:
                yield Static(f"Current role: {self._current_role}", id="role-picker-current")
            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="role-picker-cancel")
                yield Button("Character", id="role-picker-character")
                yield Button("Game Master", id="role-picker-gm", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "role-picker-cancel":
            self.dismiss(None)
        elif event.button.id == "role-picker-gm":
            self.dismiss(GAME_MASTER_ROLE)
        elif event.button.id == "role-picker-character":
            self._pick_character_name()

    def _pick_character_name(self) -> None:
        def on_dismiss(name: str | None) -> None:
            self.dismiss(name or None)

        self.app.push_screen(
            TextInputDialog(
                title=f"Character Name — {self._player_name}",
                prompt=f"Enter {self._player_name}'s character name",
                placeholder="Character name",
                submit_label="Set Role",
            ),
            on_dismiss,
        )

    def action_cancel(self) -> None:
        self.dismiss(None)
