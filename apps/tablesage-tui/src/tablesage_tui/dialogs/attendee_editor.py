from __future__ import annotations

import uuid
from dataclasses import dataclass

from tablesage_model.model import Player
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Select, Static
from textual.widgets.select import NoSelection

from ..widgets import EqualWidthButtonRow
from .generic import TextInputDialog
from .speaker_resolution import NEW_PLAYER

# The human-readable role name seeded for a campaign's GM (mirrors
# `application.sessions._seed_role_name` and `campaign_detail.py`'s equivalent
# translation of the `GAME_MASTER_ROLE` magic value -- there's no shared
# constant for this literal today, this dialog follows the same precedent).
_GAME_MASTER_LABEL = "Game Master"


@dataclass(frozen=True)
class AttendeeResult:
    """`player_id` is `None` only when `allow_new_player=True` and a free-form name was
    typed instead of picking an existing player. `player_name` is always populated
    either way -- callers that only care about a name (not a DB-backed attendance row)
    never need to cross-reference `players` themselves."""

    player_id: uuid.UUID | None
    player_name: str
    roles: tuple[str, ...]


class AttendeeDialog(ModalScreen[AttendeeResult | None]):
    """Pick a player (or, with `allow_new_player`, type a free-form name instead) and
    manage their roles. Used both for Session Detail's real, DB-backed attendees
    (`allow_new_player=False`, the default -- a session attendance row needs an actual
    `Player`) and for the player-import-from-audio wizard's pre-step candidate list
    (`allow_new_player=True` -- those are just a name+roles hint for the LLM, never
    written to the DB, so there's no player to require).

    The player field stays a live `Select` either way -- editing can reassign to a
    different player, not just change roles.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        *,
        players: list[Player],
        title: str,
        player_id: uuid.UUID | None = None,
        player_name: str = "",
        roles: list[str] | None = None,
        allow_new_player: bool = False,
    ) -> None:
        super().__init__()
        self._players = players
        self._title = title
        self._player_id = player_id
        self._player_name = player_name
        self._roles: list[str] = list(roles) if roles is not None else []
        self._allow_new_player = allow_new_player

    def compose(self) -> ComposeResult:
        with Vertical(id="attendee-dialog") as dialog:
            dialog.border_title = self._title

            if not self._players and not self._allow_new_player:
                yield Static("No players are available to add.", id="attendee-empty")
                with Horizontal(classes="dialog-actions"):
                    yield Button("Close", id="attendee-close")
                return

            with Horizontal(id="attendee-player-row"):
                yield Static("Player", classes="field-label")
                options = [("New Player", NEW_PLAYER)] if self._allow_new_player else []
                options += [(player.name, player.id) for player in self._players]
                yield Select[uuid.UUID](
                    options,
                    id="attendee-player-select",
                    value=self._initial_select_value(),
                    prompt="Choose a player…",
                    allow_blank=not self._allow_new_player,
                )

            if self._allow_new_player:
                with Horizontal(id="attendee-name-row"):
                    yield Static("New Player Name", classes="field-label")
                    yield Input(id="attendee-name", value=self._player_name)

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

    def _initial_select_value(self) -> uuid.UUID | NoSelection:
        if self._player_id is not None:
            return self._player_id
        if self._allow_new_player:
            return NEW_PLAYER
        return Select.NULL

    def on_mount(self) -> None:
        if not self._players and not self._allow_new_player:
            return
        self._update_name_visibility()
        self._reload_roles()

    # Player / free-form name

    def _selected_player_id(self) -> uuid.UUID | NoSelection:
        return self.query_one("#attendee-player-select", Select).value

    def _update_name_visibility(self) -> None:
        if not self._allow_new_player:
            return
        self.query_one("#attendee-name-row").display = self._selected_player_id() == NEW_PLAYER

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
        if self._allow_new_player and self._selected_player_id() == NEW_PLAYER:
            player_ok = bool(self.query_one("#attendee-name", Input).value.strip())
        else:
            player_ok = not self.query_one("#attendee-player-select", Select).is_blank()
        self.query_one("#attendee-save", Button).disabled = not player_ok or not self._roles

    def on_select_changed(self, event: Select.Changed) -> None:
        event.stop()
        if event.select.id == "attendee-player-select":
            self._update_name_visibility()
        self._update_save_enabled()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "attendee-name":
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
        player_id = self._selected_player_id()
        if self._allow_new_player and player_id == NEW_PLAYER:
            name = self.query_one("#attendee-name", Input).value.strip()
            if not name or not self._roles:
                return
            self.dismiss(AttendeeResult(player_id=None, player_name=name, roles=tuple(self._roles)))
            return
        if isinstance(player_id, NoSelection) or not self._roles:
            return
        player = next(p for p in self._players if p.id == player_id)
        self.dismiss(AttendeeResult(player_id=player.id, player_name=player.name, roles=tuple(self._roles)))

    def action_cancel(self) -> None:
        self.dismiss(None)
