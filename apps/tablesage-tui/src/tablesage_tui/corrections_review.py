from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from tablesage_application.session_pipeline import transcript_review
from tablesage_tools.model import Transcript
from textual.widgets import DataTable

from .dialogs import SpellingSuggestionDialog, SpellingSuggestionResult

if TYPE_CHECKING:
    from tablesage_application.session_pipeline.suggest_spelling_corrections import SpellingSuggestion
    from textual.screen import Screen


@dataclass(frozen=True)
class DraftCorrection:
    id: uuid.UUID
    from_text: str
    to_text: str
    case_sensitive: bool


class CorrectionsReview:
    """In-memory New/Edit/Delete review of LLM-proposed find/replace corrections in a `DataTable`.

    Shared by Manual Review's spelling suggestions and Process Session's Review Name Corrections.
    Reviewed the same way `GlossaryReviewScreen` reviews its own LLM proposals: the table is fully
    rebuilt on each change, and occurrence counts are recomputed live against *transcript* (not the
    snapshot the LLM call produced) so editing a row's `from_text` or `case_sensitive` immediately
    shows what applying would actually do. The host screen owns the bindings and applying.
    """

    def __init__(self, screen: Screen[Any], table_selector: str, noun: str, *, whole_words: bool = False) -> None:
        self._screen = screen
        self._table_selector = table_selector
        self._noun = noun
        # Must match how the host screen applies the corrections, or the Occurrences column misreports.
        self._whole_words = whole_words
        self.corrections: list[DraftCorrection] = []
        self.transcript: Transcript | None = None

    @staticmethod
    def add_columns(table: DataTable[str]) -> None:
        table.add_column("From", key="from")
        table.add_column("To", key="to")
        table.add_column("Occurrences", key="occurrences")
        table.add_column("Case Sensitive", key="case_sensitive")

    def _table(self) -> DataTable[str]:
        return self._screen.query_one(self._table_selector, DataTable)

    def load(self, transcript: Transcript, suggestions: Sequence[SpellingSuggestion]) -> None:
        self.transcript = transcript
        self.corrections = [
            DraftCorrection(id=uuid.uuid4(), from_text=s.from_text, to_text=s.to_text, case_sensitive=s.case_sensitive) for s in suggestions
        ]
        self._sort()
        self.reload()

    def _sort(self) -> None:
        self.corrections.sort(key=lambda correction: correction.from_text.casefold())

    def _selected_id(self) -> uuid.UUID | None:
        table = self._table()
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return uuid.UUID(row_key) if row_key else None

    def selected(self) -> DraftCorrection | None:
        correction_id = self._selected_id()
        return next((correction for correction in self.corrections if correction.id == correction_id), None)

    def reload(self, selected_id: uuid.UUID | None = None) -> None:
        assert self.transcript is not None
        table = self._table()
        selected_id = selected_id or self._selected_id()
        table.clear()
        restored_row: int | None = None
        for index, correction in enumerate(self.corrections):
            occurrence_count = transcript_review.count_occurrences(
                self.transcript, correction.from_text, correction.case_sensitive, whole_words=self._whole_words
            )
            table.add_row(
                correction.from_text,
                correction.to_text,
                str(occurrence_count),
                "✓" if correction.case_sensitive else "",
                key=str(correction.id),
            )
            if correction.id == selected_id:
                restored_row = index
        if restored_row is not None:
            table.move_cursor(row=restored_row)
        self._screen.refresh_bindings()

    def new(self) -> None:
        def on_dismiss(result: SpellingSuggestionResult | None) -> None:
            if result is None:
                return
            correction = DraftCorrection(
                id=uuid.uuid4(), from_text=result.from_text, to_text=result.to_text, case_sensitive=result.case_sensitive
            )
            self.corrections.append(correction)
            self._sort()
            self.reload(correction.id)

        self._screen.app.push_screen(SpellingSuggestionDialog(title=f"New {self._noun}", submit_label=f"Add {self._noun}"), on_dismiss)

    def edit_selected(self) -> None:
        correction = self.selected()
        if correction is None:
            return

        def on_dismiss(result: SpellingSuggestionResult | None) -> None:
            if result is None:
                return
            index = self.corrections.index(correction)
            self.corrections[index] = replace(
                correction, from_text=result.from_text, to_text=result.to_text, case_sensitive=result.case_sensitive
            )
            self._sort()
            self.reload(correction.id)

        self._screen.app.push_screen(
            SpellingSuggestionDialog(
                title=f"Edit {self._noun}",
                submit_label="Save",
                from_text=correction.from_text,
                to_text=correction.to_text,
                case_sensitive=correction.case_sensitive,
            ),
            on_dismiss,
        )

    def delete_selected(self) -> None:
        correction = self.selected()
        if correction is None:
            return
        index = self.corrections.index(correction)
        self.corrections.remove(correction)
        self.reload()
        table = self._table()
        if table.row_count:
            table.move_cursor(row=min(index, table.row_count - 1))


def applied_message(correction_count: int, occurrence_total: int) -> str | None:
    """The notification after applying corrections, or None when nothing was replaced."""
    if not occurrence_total:
        return None
    occurrence_plural = "" if occurrence_total == 1 else "s"
    correction_plural = "" if correction_count == 1 else "s"
    return f"Applied {correction_count} correction{correction_plural}, {occurrence_total} occurrence{occurrence_plural}."
