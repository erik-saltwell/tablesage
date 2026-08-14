from __future__ import annotations

from dataclasses import dataclass

from tablesage_model.model import GlossaryEntry
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static, TextArea


@dataclass(frozen=True)
class GlossaryEntryDialogResult:
    original_term: str | None
    term: str
    description: str


class GlossaryEntryDialog(ModalScreen[GlossaryEntryDialogResult | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        *,
        existing_terms: frozenset[str],
        original_entry: GlossaryEntry | None = None,
    ) -> None:
        super().__init__()
        self._existing_terms = existing_terms
        self._original_entry = original_entry

    def compose(self) -> ComposeResult:
        title = "Edit Glossary Entry" if self._original_entry else "Add Glossary Entry"
        with Vertical(id="glossary-entry-dialog") as dialog:
            dialog.border_title = title
            yield Static(id="term_lbl", classes="label", content="Term")
            yield Input(
                value=self._original_entry.term if self._original_entry else "",
                placeholder="Term",
                id="glossary-term",
            )
            yield Static(id="description_lbl", classes="label", content="Description")
            yield TextArea(
                text=self._original_entry.description if self._original_entry else "",
                placeholder="Description",
                id="glossary-description",
            )
            yield Static("", id="glossary-entry-error")

            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="cancel-glossary-entry")
                yield Button("Save", id="save-glossary-entry", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#glossary-term", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-glossary-entry":
            self.dismiss(None)
            return

        if event.button.id == "save-glossary-entry":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        term_input = self.query_one("#glossary-term", Input)
        description_input = self.query_one("#glossary-description", TextArea)
        error = self.query_one("#glossary-entry-error", Static)

        term = term_input.value.strip()
        description = description_input.text.strip()
        original_term = self._original_entry.term if self._original_entry else None

        if not term:
            error.update("Term is required.")
            term_input.focus()
            return

        if term in self._existing_terms and term != original_term:
            error.update("A glossary entry with that term already exists.")
            term_input.focus()
            return

        self.dismiss(
            GlossaryEntryDialogResult(
                original_term=original_term,
                term=term,
                description=description,
            )
        )


class ConfirmDeleteGlossaryEntryDialog(ModalScreen[str | None]):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, term: str) -> None:
        super().__init__()
        self._term = term

    def compose(self) -> ComposeResult:
        with Vertical(id="delete-glossary-entry-dialog") as dialog:
            dialog.border_title = "Delete Glossary Entry"
            yield Static(f"Delete '{self._term}'?", id="delete-glossary-entry-message")
            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="cancel-delete-glossary-entry")
                yield Button("Delete", id="confirm-delete-glossary-entry", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-delete-glossary-entry":
            self.dismiss(None)
            return

        if event.button.id == "confirm-delete-glossary-entry":
            self.dismiss(self._term)

    def action_cancel(self) -> None:
        self.dismiss(None)
