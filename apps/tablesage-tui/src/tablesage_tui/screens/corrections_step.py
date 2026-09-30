from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from ..corrections_review import CorrectionsReview
from ..processing.drafts import DraftSlot, leave_with_draft
from .base import TableSageScreen

if TYPE_CHECKING:
    from tablesage_application.session_pipeline.suggest_spelling_corrections import SpellingSuggestion
    from tablesage_tools.model import Transcript


class CorrectionsStepScreen(TableSageScreen):
    """A processing step's review of find/replace corrections to a transcript.

    Used by Review Name Corrections and Spellcheck Against Glossary. The suggestion step made the LLM call before
    this opens, so it only reviews: New, Edit, and Keep/Remove rows. Apply & Continue dismisses with the reviewed rows,
    which the step saves; Cancel dismisses with None, first offering to keep changed rows as a draft.
    """

    HIDDEN_BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]
    COMMON_BINDINGS = [
        Binding("c,C", "confirm", "Continue", key_display="C"),
        Binding("n,N", "new_correction", "New Correction", key_display="N"),
        Binding("enter,e,E", "edit_correction", "Edit Correction", key_display="E"),
        Binding("d,D,delete,backspace", "delete_correction", "Delete Correction", key_display="D"),
    ]

    def __init__(
        self,
        *,
        title: str,
        hint: str,
        transcript: Transcript,
        suggestions: Sequence[SpellingSuggestion],
        whole_words: bool,
        draft: DraftSlot | None = None,
        soft_remove: bool = False,
    ) -> None:
        super().__init__()
        self.section = f"process session · {title.lower()}"
        self._title = title
        self._hint = hint
        self._transcript = transcript
        self._suggestions = list(suggestions)
        self._draft = draft
        self._soft_remove = soft_remove
        self._corrections = CorrectionsReview(
            self, "#corrections-step-table", noun="Correction", whole_words=whole_words, soft_remove=soft_remove
        )

    def compose_content(self) -> ComposeResult:
        with Vertical(id="corrections-step-panel", classes="panel surface-2") as panel:
            panel.border_title = f" {self._title} "
            yield Static(self._hint, classes="section-title")
            table: DataTable[object] = DataTable(
                id="corrections-step-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table"
            )
            CorrectionsReview.add_columns(table, soft_remove=self._soft_remove)
            yield table
            with Horizontal(id="corrections-step-actions"):
                yield Button("Cancel", id="corrections-step-cancel")
                yield Button("Continue", id="corrections-step-confirm", variant="primary")

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

    def _rows(self) -> list[tuple[str, str, bool, bool]]:
        return [(row.from_text, row.to_text, row.case_sensitive, row.removed) for row in self._corrections.corrections]

    def action_confirm(self) -> None:
        self.dismiss(list(self._corrections.corrections))

    def action_cancel(self) -> None:
        initial = sorted((s.from_text, s.to_text, s.case_sensitive, s.removed) for s in self._suggestions)
        leave_with_draft(
            self,
            changed=sorted(self._rows()) != initial,
            slot=self._draft,
            value=lambda: [{"from_text": f, "to_text": t, "case_sensitive": c, "removed": removed} for f, t, c, removed in self._rows()],
            leave=lambda: self.dismiss(None),
        )
