from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from ..corrections_review import CorrectionsReview, applied_message
from .base import TableSageScreen

if TYPE_CHECKING:
    from tablesage_application.session_pipeline.suggest_spelling_corrections import Correction, SpellingSuggestion
    from tablesage_tools.model import Transcript


class CorrectionsStepScreen(TableSageScreen):
    """A Process Session step that reviews the LLM's find/replace corrections to a transcript.

    Used by Review Name Corrections (step 2) and Spellcheck Against Glossary (step 4). Process Session
    makes the LLM call before opening this screen, so it only reviews: New, Edit, and Delete rows, then
    Apply & Continue saves through `save` and hands control back to the caller, which continues
    processing. Cancel returns without writing anything.
    """

    COMMON_BINDINGS = [
        Binding("n,N", "new_correction", "New", key_display="N"),
        Binding("enter,e,E", "edit_correction", "Edit", key_display="E"),
        Binding("d,D,delete,backspace", "delete_correction", "Delete", key_display="D"),
        Binding("c,C", "confirm", "Apply & Continue", key_display="C"),
        Binding("escape", "cancel", "Cancel", key_display="Esc"),
    ]

    def __init__(
        self,
        *,
        title: str,
        hint: str,
        transcript: Transcript,
        suggestions: list[SpellingSuggestion],
        whole_words: bool,
        save: Callable[[Sequence[Correction]], tuple[bool, int]],
        on_confirmed: Callable[[], None],
    ) -> None:
        super().__init__()
        self.section = f"process session · {title.lower()}"
        self._title = title
        self._hint = hint
        self._transcript = transcript
        self._suggestions = suggestions
        self._save = save
        self._on_confirmed = on_confirmed
        self._corrections = CorrectionsReview(self, "#corrections-step-table", noun="Correction", whole_words=whole_words)

    def compose_content(self) -> ComposeResult:
        with Vertical(id="corrections-step-panel", classes="panel surface-2") as panel:
            panel.border_title = f" {self._title} "
            yield Static(self._hint, classes="section-title")
            table: DataTable[str] = DataTable(id="corrections-step-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            CorrectionsReview.add_columns(table)
            yield table
            with Horizontal(id="corrections-step-actions"):
                yield Button("Cancel", id="corrections-step-cancel")
                yield Button("Apply & Continue", id="corrections-step-confirm", variant="primary")

    def on_mount(self) -> None:
        self._corrections.load(self._transcript, self._suggestions)
        self.query_one("#corrections-step-table", DataTable).focus()

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
        if event.button.id == "corrections-step-confirm":
            self.action_confirm()
        elif event.button.id == "corrections-step-cancel":
            self.action_cancel()

    def action_confirm(self) -> None:
        corrections = self._corrections.corrections
        try:
            _written, occurrence_total = self._save(corrections)
        except (OSError, ValueError) as exc:
            self.notify(f"Could not save the corrections: {exc}", severity="error")
            return
        message = applied_message(len(corrections), occurrence_total)
        if message is not None:
            self.notify(message)
        self.app.pop_screen()
        self._on_confirmed()

    def action_cancel(self) -> None:
        self.app.pop_screen()
