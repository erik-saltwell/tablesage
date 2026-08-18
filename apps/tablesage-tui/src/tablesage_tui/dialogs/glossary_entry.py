from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


class GlossaryEntryDialog(ModalScreen[tuple[str, str | None] | None]):
    """Two-field term/description entry, used for both create and edit."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, *, title: str, term: str = "", description: str = "", submit_label: str = "Save") -> None:
        super().__init__()
        self._title = title
        self._term = term
        self._description = description
        self._submit_label = submit_label

    def compose(self) -> ComposeResult:
        with Vertical(id="glossary-entry-dialog") as dialog:
            dialog.border_title = self._title
            yield Static("Term", classes="field-label")
            yield Input(id="glossary-entry-term", value=self._term, placeholder="Term")
            yield Static("Description", classes="field-label")
            yield Input(id="glossary-entry-description", value=self._description, placeholder="Description (optional)")
            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="glossary-entry-cancel")
                yield Button(self._submit_label, id="glossary-entry-submit", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#glossary-entry-term", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "glossary-entry-cancel":
            self.dismiss(None)
        elif event.button.id == "glossary-entry-submit":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        term = self.query_one("#glossary-entry-term", Input).value.strip()
        if not term:
            self.notify("Term cannot be blank.", severity="error")
            return
        description = self.query_one("#glossary-entry-description", Input).value.strip()
        self.dismiss((term, description or None))
