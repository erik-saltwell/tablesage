from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tablesage_model.model import Player
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Select, Static
from textual.widgets.select import NoSelection

from ..widgets import EqualWidthButtonRow
from .generic import TextInputDialog

if TYPE_CHECKING:
    from tablesage_application.entities.sessions import Attendee

# The human-readable role name seeded for a campaign's GM (mirrors
# `application.sessions._seed_role_name` and `campaign_detail.py`'s equivalent
# translation of the `GAME_MASTER_ROLE` magic value -- there's no shared
# constant for this literal today, this dialog follows the same precedent).
_GAME_MASTER_LABEL = "Game Master"


@dataclass(frozen=True)
class AttendeeResult:
    player_id: uuid.UUID
    roles: tuple[str, ...]


class AttendeeDialog(ModalScreen[AttendeeResult | None]):
    """Add a new attendee or edit an existing one: pick a player, manage their roles.

    One dialog for both flows (see `.documentation/session_detail_screen.md`):
    `attendee=None` is Add (no player preselected, roles start empty);
    otherwise it's Edit, preseeded with the current player and roles. The
    player field stays a live `Select` in both modes -- editing can reassign
    the attendance row to a different roster player, not just its roles.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, players: list[Player], attendee: Attendee | None) -> None:
        super().__init__()
        self._players = players
        self._attendee = attendee
        self._roles: list[str] = list(attendee.roles) if attendee is not None else []

    def compose(self) -> ComposeResult:
        with Vertical(id="attendee-dialog") as dialog:
            dialog.border_title = "Edit Attendee" if self._attendee is not None else "Add Attendee"

            if not self._players:
                yield Static("No players are available to add.", id="attendee-empty")
                with Horizontal(classes="dialog-actions"):
                    yield Button("Close", id="attendee-close")
                return

            with Horizontal(id="attendee-player-row"):
                yield Static("Player", classes="field-label")
                yield Select[uuid.UUID](
                    [(player.name, player.id) for player in self._players],
                    id="attendee-player-select",
                    value=self._attendee.player_id if self._attendee is not None else Select.NULL,
                    prompt="Choose a player…",
                )

            yield Static("Roles", classes="section-title")
            table: DataTable[str] = DataTable(id="attendee-role-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_column("Role", key="role")
            yield table

            with EqualWidthButtonRow(id="attendee-role-actions"):
                with Horizontal(id="attendee-role-actions-add"):
                    yield Button("Add Role", id="attendee-add-role")
                    yield Button("Add Game Master", id="attendee-add-gm")
                with Horizontal(id="attendee-role-actions-edit"):
                    yield Button("Edit", id="attendee-edit-role")
                    yield Button("Remove", id="attendee-remove-role")

            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Cancel", id="attendee-cancel")
                yield Button("Save", id="attendee-save", variant="primary", disabled=True)

    def on_mount(self) -> None:
        if not self._players:
            return
        self._reload_roles()

    # Roles (held in-memory here; only written to the DB by the caller after Save)

    def _reload_roles(self) -> None:
        table = self.query_one("#attendee-role-table", DataTable)
        table.clear()
        for role in self._roles:
            table.add_row(role, key=role)
        self._update_save_enabled()

    def _selected_role(self) -> str | None:
        table = self.query_one("#attendee-role-table", DataTable)
        if table.row_count == 0:
            return None
        return table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value

    def _add_role(self, name: str) -> None:
        name = name.strip()
        if not name or name in self._roles:
            return
        self._roles.append(name)
        self._reload_roles()

    def _add_custom_role(self) -> None:
        def on_named(name: str | None) -> None:
            if name:
                self._add_role(name)

        self.app.push_screen(
            TextInputDialog(title="Add Role", prompt="Enter a role name", submit_label="Add"),
            on_named,
        )

    def _edit_selected_role(self) -> None:
        current = self._selected_role()
        if current is None:
            return

        def on_renamed(name: str | None) -> None:
            if not name or name == current:
                return
            if name in self._roles:
                self.notify(f"'{name}' is already one of this attendee's roles.", severity="error")
                return
            self._roles[self._roles.index(current)] = name
            self._reload_roles()

        self.app.push_screen(
            TextInputDialog(title="Edit Role", prompt="Role name", submit_label="Save", initial_value=current),
            on_renamed,
        )

    def _remove_selected_role(self) -> None:
        current = self._selected_role()
        if current is None:
            return
        self._roles.remove(current)
        self._reload_roles()

    # Save gating

    def _update_save_enabled(self) -> None:
        select = self.query_one("#attendee-player-select", Select)
        self.query_one("#attendee-save", Button).disabled = select.is_blank() or not self._roles

    def on_select_changed(self, event: Select.Changed) -> None:
        event.stop()
        self._update_save_enabled()

    # Dismissal

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id in ("attendee-cancel", "attendee-close"):
            self.dismiss(None)
        elif button_id == "attendee-add-role":
            self._add_custom_role()
        elif button_id == "attendee-add-gm":
            self._add_role(_GAME_MASTER_LABEL)
        elif button_id == "attendee-edit-role":
            self._edit_selected_role()
        elif button_id == "attendee-remove-role":
            self._remove_selected_role()
        elif button_id == "attendee-save":
            self._submit()

    def _submit(self) -> None:
        select = self.query_one("#attendee-player-select", Select)
        player_id = select.value
        if isinstance(player_id, NoSelection) or not self._roles:
            return
        self.dismiss(AttendeeResult(player_id=player_id, roles=tuple(self._roles)))

    def action_cancel(self) -> None:
        self.dismiss(None)
