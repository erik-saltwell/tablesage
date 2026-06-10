from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class ConfirmationDialog(ModalScreen[bool | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, title: str, prompt: str, show_cancel: bool = True) -> None:
        super().__init__()
        self._title = title
        self._prompt = prompt
        self._show_cancel = show_cancel

    def compose(self) -> ComposeResult:
        with Vertical(id="confirmation-dialog") as dialog:
            dialog.border_title = self._title
            yield Static(self._prompt, id="confirmation-prompt")
            with Horizontal(classes="dialog-actions"):
                if self._show_cancel:
                    yield Button("Cancel", id="confirmation-cancel")
                yield Button("No", id="confirmation-no")
                yield Button("Yes", id="confirmation-yes", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirmation-yes":
            self.dismiss(True)
            return

        if event.button.id == "confirmation-no":
            self.dismiss(False)
            return

        if event.button.id == "confirmation-cancel":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class TextInputDialog(ModalScreen[str | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, title: str, prompt: str, placeholder: str = "") -> None:
        super().__init__()
        self._title = title
        self._prompt = prompt
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(id="text-input-dialog") as dialog:
            dialog.border_title = self._title
            yield Static(self._prompt, id="text-input-prompt")
            yield Input(id="text-input-value", placeholder=self._placeholder)
            with Horizontal(classes="dialog-actions"):
                yield Button("No", id="text-input-no")
                yield Button("Yes", id="text-input-yes", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#text-input-value", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "text-input-no":
            self.dismiss(None)
            return

        if event.button.id == "text-input-yes":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        self.dismiss(self.query_one("#text-input-value", Input).value.strip())
