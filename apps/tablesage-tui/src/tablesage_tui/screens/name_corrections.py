from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from ..corrections_review import CorrectionsReview, applied_message
from .base import TableSageScreen

if TYPE_CHECKING:
    from tablesage_application.session_pipeline.suggest_spelling_corrections import SpellingSuggestion
    from tablesage_tools.model import Transcript


class NameCorrectionsScreen(TableSageScreen):
    """Step 2 of Process Session: review the LLM's corrections to misheard player and character names.

    Process Session makes the LLM call before opening this screen, so it only reviews: New, Edit, and
    Delete rows, then Apply & Continue writes the name-corrected transcript and hands control back to
    the caller, which continues processing. Cancel returns without writing anything.
    """

    section = "process session · name corrections"
    COMMON_BINDINGS = [
        Binding("n,N", "new_correction", "New", key_display="N"),
        Binding("enter,e,E", "edit_correction", "Edit", key_display="E"),
        Binding("d,D,delete,backspace", "delete_correction", "Delete", key_display="D"),
        Binding("c,C", "confirm", "Apply & Continue", key_display="C"),
        Binding("escape", "cancel", "Cancel", key_display="Esc"),
    ]

    def __init__(
        self, session_id: uuid.UUID, transcript: Transcript, suggestions: list[SpellingSuggestion], on_confirmed: Callable[[], None]
    ) -> None:
        super().__init__()
        self._session_id = session_id
        self._transcript = transcript
        self._suggestions = suggestions
        self._on_confirmed = on_confirmed
        self._corrections = CorrectionsReview(self, "#name-corrections-table", noun="Correction", whole_words=True)

    def compose_content(self) -> ComposeResult:
        with Vertical(id="name-corrections-panel", classes="panel surface-2") as panel:
            panel.border_title = " Name Corrections "
            yield Static("Keep only corrections to names that were misheard; they apply to every later step.", classes="section-title")
            table: DataTable[str] = DataTable(id="name-corrections-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            CorrectionsReview.add_columns(table)
            yield table
            with Horizontal(id="name-corrections-actions"):
                yield Button("Cancel", id="name-corrections-cancel")
                yield Button("Apply & Continue", id="name-corrections-confirm", variant="primary")

    def on_mount(self) -> None:
        self._corrections.load(self._transcript, self._suggestions)
        self.query_one("#name-corrections-table", DataTable).focus()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in {"edit_correction", "delete_correction"}:
            return True if self._corrections.selected() is not None else None
        return super().check_action(action, parameters)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enter (or a second click on the selected row) opens that row's editor."""
        event.stop()
        self.action_edit_correction()

    def action_new_correction(self) -> None:
        self._corrections.new()

    def action_edit_correction(self) -> None:
        self._corrections.edit_selected()

    def action_delete_correction(self) -> None:
        self._corrections.delete_selected()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "name-corrections-confirm":
            self.action_confirm()
        elif event.button.id == "name-corrections-cancel":
            self.action_cancel()

    def action_confirm(self) -> None:
        corrections = self._corrections.corrections
        try:
            _written, occurrence_total = self.application.save_name_corrections(self._session_id, corrections)
        except (OSError, ValueError) as exc:
            self.notify(f"Could not save the name corrections: {exc}", severity="error")
            return
        message = applied_message(len(corrections), occurrence_total)
        if message is not None:
            self.notify(message)
        self.app.pop_screen()
        self._on_confirmed()

    def action_cancel(self) -> None:
        self.app.pop_screen()
