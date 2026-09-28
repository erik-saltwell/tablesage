from __future__ import annotations

from collections.abc import Awaitable, Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from ..widgets import EqualWidthButtonRow

OnPlayerSubmit = Callable[[str], Awaitable[str | None]]


class PlayerDialog(ModalScreen[None]):
    """Collect a player's name for both creation and metadata editing.

    Does its own field-level validation (non-blank) only. Everything else -- name-format rules,
    the application call, and any folder-collision confirmation -- is the caller's `on_submit`,
    awaited here: `None` dismisses the dialog, a string is shown as an inline error and the
    dialog stays open with the typed name intact (see `intent.md` in the
    `metadata-below-lists` work item for why dialogs don't own application calls directly).
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, title: str, on_submit: OnPlayerSubmit, name: str = "", submit_label: str = "Save") -> None:
        super().__init__()
        self._title = title
        self._on_submit = on_submit
        self._name = name
        self._submit_label = submit_label

    def compose(self) -> ComposeResult:
        with Vertical(id="player-dialog") as dialog:
            dialog.border_title = self._title
            with Horizontal(classes="field-row"):
                yield Static("Name", classes="field-label")
                yield Input(id="player-dialog-name", value=self._name)
            yield Static("", id="player-dialog-error", classes="dialog-error", markup=False)
            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Cancel", id="player-dialog-cancel")
                yield Button(self._submit_label, id="player-dialog-submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#player-dialog-name", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "player-dialog-cancel":
            self.dismiss(None)
        elif event.button.id == "player-dialog-submit":
            self.run_worker(self._submit())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.run_worker(self._submit())

    def action_cancel(self) -> None:
        self.dismiss(None)

    async def _submit(self) -> None:
        name = self.query_one("#player-dialog-name", Input).value.strip()
        if not name:
            self._show_error("Name is required.")
            return

        submit_button = self.query_one("#player-dialog-submit", Button)
        submit_button.disabled = True
        try:
            error = await self._on_submit(name)
        finally:
            submit_button.disabled = False

        if error is None:
            self.dismiss(None)
        else:
            self._show_error(error)

    def _show_error(self, message: str) -> None:
        self.query_one("#player-dialog-error", Static).update(message)
