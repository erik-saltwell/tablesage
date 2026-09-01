from __future__ import annotations

import re
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, replace

from tablesage_application.session_pipeline.extract_glossary import GlossaryProposal
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable

from ..dialogs import FindReplaceDialog, FindReplaceResult, GlossaryEntryDialog
from .base import TableSageScreen


@dataclass(frozen=True)
class _DraftEntry:
    id: uuid.UUID
    term: str
    description: str | None


class GlossaryReviewScreen(TableSageScreen):
    """Review an in-memory glossary proposal before committing it to the campaign."""

    section = "session detail"

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", key_display="Esc", show=False),
        Binding("n,N", "new_entry", "New", key_display="N"),
        Binding("enter,e,E", "edit_entry", "Edit", key_display="E"),
        Binding("d,D,delete,backspace", "delete_entry", "Delete", key_display="D"),
        Binding("f,F", "find_replace", "Find/Replace", key_display="F"),
        Binding("c,C", "complete", "Complete", key_display="C"),
    ]

    def __init__(self, session_id: uuid.UUID, proposals: Sequence[GlossaryProposal]) -> None:
        super().__init__()
        self._session_id = session_id
        self._entries = [_DraftEntry(id=uuid.uuid4(), term=proposal.term, description=proposal.description) for proposal in proposals]
        self._sort_entries()

    def compose_content(self) -> ComposeResult:
        with Vertical(id="glossary-review-panel", classes="panel surface-2") as panel:
            panel.border_title = " review glossary entries "
            table: DataTable[str] = DataTable(id="glossary-review-table", cursor_type="row", zebra_stripes=True, classes="tablesage-table")
            table.add_column("Term", key="term")
            table.add_column("Description", key="description")
            yield table

    def on_mount(self) -> None:
        self._reload_table()

    def _sort_entries(self) -> None:
        self._entries.sort(key=lambda entry: entry.term.casefold())

    def _selected_entry_id(self) -> uuid.UUID | None:
        table = self.query_one("#glossary-review-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value
        return uuid.UUID(row_key) if row_key else None

    def _selected_entry(self) -> _DraftEntry | None:
        entry_id = self._selected_entry_id()
        return next((entry for entry in self._entries if entry.id == entry_id), None)

    def _reload_table(self, selected_id: uuid.UUID | None = None) -> None:
        table = self.query_one("#glossary-review-table", DataTable)
        selected_id = selected_id or self._selected_entry_id()
        table.clear()
        restored_row: int | None = None
        for index, entry in enumerate(self._entries):
            table.add_row(entry.term, entry.description or "", key=str(entry.id))
            if entry.id == selected_id:
                restored_row = index
        if restored_row is not None:
            table.move_cursor(row=restored_row)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        event.stop()
        self.action_edit_entry()

    def action_new_entry(self) -> None:
        def on_dismiss(result: tuple[str, str | None] | None) -> None:
            if result is None:
                return
            entry = _DraftEntry(id=uuid.uuid4(), term=result[0], description=result[1])
            self._entries.append(entry)
            self._sort_entries()
            self._reload_table(entry.id)

        self.app.push_screen(GlossaryEntryDialog(title="New Glossary Entry", submit_label="Add Entry"), on_dismiss)

    def action_edit_entry(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return

        def on_dismiss(result: tuple[str, str | None] | None) -> None:
            if result is None:
                return
            index = self._entries.index(entry)
            self._entries[index] = replace(entry, term=result[0], description=result[1])
            self._sort_entries()
            self._reload_table(entry.id)

        self.app.push_screen(
            GlossaryEntryDialog(
                title="Edit Glossary Entry",
                term=entry.term,
                description=entry.description or "",
            ),
            on_dismiss,
        )

    def action_delete_entry(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        index = self._entries.index(entry)
        self._entries.remove(entry)
        self._reload_table()
        table = self.query_one("#glossary-review-table", DataTable)
        if table.row_count:
            table.move_cursor(row=min(index, table.row_count - 1))

    def action_find_replace(self) -> None:
        def on_dismiss(result: FindReplaceResult | None) -> None:
            if result is None:
                return
            flags = 0 if result.case_sensitive else re.IGNORECASE
            pattern = re.compile(re.escape(result.find), flags)
            occurrence_count = 0
            changed_entry_count = 0
            replaced_entries: list[_DraftEntry] = []
            for entry in self._entries:
                term, term_count = pattern.subn(result.replace, entry.term)
                description = entry.description
                description_count = 0
                if description is not None:
                    description, description_count = pattern.subn(result.replace, description)
                occurrence_count += term_count + description_count
                changed_entry_count += bool(term_count or description_count)
                replaced_entries.append(replace(entry, term=term, description=description))

            if occurrence_count == 0:
                self.notify("No matches found.", severity="warning")
                return

            self._entries = replaced_entries
            self._sort_entries()
            self._reload_table()
            occurrence_plural = "" if occurrence_count == 1 else "s"
            entry_word = "entry" if changed_entry_count == 1 else "entries"
            self.notify(f"Replaced {occurrence_count} occurrence{occurrence_plural} in {changed_entry_count} {entry_word}.")

        self.app.push_screen(FindReplaceDialog(), on_dismiss)

    def action_complete(self) -> None:
        if any(not entry.term.strip() for entry in self._entries):
            self.notify("Glossary terms cannot be blank.", severity="error")
            return
        proposals = [GlossaryProposal(term=entry.term.strip(), description=entry.description) for entry in self._entries]
        result = self.application.complete_glossary_extraction(self._session_id, proposals)
        self.app.pop_screen()
        added_word = "entry" if result.added_count == 1 else "entries"
        message = f"Added {result.added_count} glossary {added_word}."
        if result.skipped_duplicate_count:
            duplicate_word = "duplicate" if result.skipped_duplicate_count == 1 else "duplicates"
            message += f" Skipped {result.skipped_duplicate_count} {duplicate_word}."
        self.app.notify(message)

    def action_cancel(self) -> None:
        self.app.pop_screen()
