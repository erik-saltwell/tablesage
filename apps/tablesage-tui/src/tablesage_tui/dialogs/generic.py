from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class _DialogActions(Horizontal):
    """An action row whose buttons share the widest content-sized width."""

    def on_mount(self) -> None:
        self.call_after_refresh(self._equalize_button_widths)

    def _equalize_button_widths(self) -> None:
        buttons = list(self.query(Button))
        widest_width = max((button.region.width for button in buttons), default=0)
        for button in buttons:
            button.styles.width = widest_width


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
            with _DialogActions(classes="dialog-actions"):
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

    def __init__(
        self,
        *,
        title: str,
        prompt: str,
        placeholder: str = "",
        submit_label: str = "Submit",
    ) -> None:
        super().__init__()
        self._title = title
        self._prompt = prompt
        self._placeholder = placeholder
        self._submit_label = submit_label

    def compose(self) -> ComposeResult:
        with Vertical(id="text-input-dialog") as dialog:
            dialog.border_title = self._title
            yield Static(self._prompt, id="text-input-prompt")
            yield Input(id="text-input-value", placeholder=self._placeholder)
            with _DialogActions(classes="dialog-actions"):
                yield Button("Cancel", id="text-input-cancel")
                yield Button(
                    self._submit_label,
                    id="text-input-submit",
                    variant="primary",
                    disabled=True,
                )

    def on_mount(self) -> None:
        self.query_one("#text-input-value", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.query_one("#text-input-submit", Button).disabled = not event.value.strip()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "text-input-cancel":
            self.dismiss(None)
            return

        if event.button.id == "text-input-submit":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        if event.value.strip():
            self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        self.dismiss(self.query_one("#text-input-value", Input).value.strip())
