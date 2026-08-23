from __future__ import annotations

import uuid
from dataclasses import dataclass

from tablesage_model.model import Player
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select, Static
from textual.widgets.select import NoSelection

from ..player_import_run import SpeakerResolution
from ..widgets import EqualWidthButtonRow

# Never a real player id (those are uuid4) -- the "New Player" option in the `Select` below.
NEW_PLAYER: uuid.UUID = uuid.UUID(int=0)


@dataclass(frozen=True)
class SpeakerResolutionResult:
    player_id: uuid.UUID | None
    player_name: str
    excluded: bool


class SpeakerResolutionDialog(ModalScreen[SpeakerResolutionResult | None]):
    """Stage 4's per-speaker editor.

    `DataTable` cells can't host a live `Select`/`Input`/toggle, so editing a review row
    pushes this dialog instead -- mirroring `AttendeeDialog`'s own workaround for the same
    constraint (see `.documentation/import_players_from_audio_file.md`).
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, players: list[Player], current: SpeakerResolution) -> None:
        super().__init__()
        self._players = players
        self._current = current

    def compose(self) -> ComposeResult:
        with Vertical(id="speaker-resolution-dialog") as dialog:
            dialog.border_title = "Resolve Speaker"

            with Horizontal(id="speaker-resolution-player-row"):
                yield Static("Player", classes="field-label")
                yield Select[uuid.UUID](
                    [("New Player", NEW_PLAYER), *((player.name, player.id) for player in self._players)],
                    id="speaker-resolution-player-select",
                    value=self._current.player_id if self._current.player_id is not None else NEW_PLAYER,
                    allow_blank=False,
                )

            with Horizontal(id="speaker-resolution-name-row"):
                yield Static("New Player Name", classes="field-label")
                yield Input(id="speaker-resolution-name", value=self._current.player_name)

            with Horizontal(id="speaker-resolution-status-row"):
                yield Static("Status", classes="field-label")
                yield Select[bool](
                    [("Include", False), ("Exclude", True)],
                    id="speaker-resolution-status-select",
                    value=self._current.excluded,
                    allow_blank=False,
                )

            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Cancel", id="speaker-resolution-cancel")
                yield Button("Save", id="speaker-resolution-save", variant="primary")

    def on_mount(self) -> None:
        self._update_name_visibility()

    def on_select_changed(self, event: Select.Changed) -> None:
        event.stop()
        if event.select.id == "speaker-resolution-player-select":
            self._update_name_visibility()

    def _selected_player_id(self) -> uuid.UUID:
        value = self.query_one("#speaker-resolution-player-select", Select).value
        return NEW_PLAYER if isinstance(value, NoSelection) else value

    def _update_name_visibility(self) -> None:
        self.query_one("#speaker-resolution-name-row").display = self._selected_player_id() == NEW_PLAYER

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "speaker-resolution-cancel":
            self.dismiss(None)
        elif event.button.id == "speaker-resolution-save":
            self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        player_id = self._selected_player_id()
        excluded = bool(self.query_one("#speaker-resolution-status-select", Select).value)

        if player_id == NEW_PLAYER:
            name = self.query_one("#speaker-resolution-name", Input).value.strip()
            if not name:
                self.notify("Enter a name for the new player.", severity="error")
                return
            self.dismiss(SpeakerResolutionResult(player_id=None, player_name=name, excluded=excluded))
            return

        player = next(p for p in self._players if p.id == player_id)
        self.dismiss(SpeakerResolutionResult(player_id=player.id, player_name=player.name, excluded=excluded))
