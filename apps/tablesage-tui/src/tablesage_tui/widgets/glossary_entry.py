from __future__ import annotations

from tablesage_model.model import GlossaryEntry
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import Click
from textual.message import Message
from textual.widgets import Button, Static

from .empty_widget import EmptyWidget


class GlossaryEntryWidget(Vertical):
    class Selected(Message):
        def __init__(self, term: str) -> None:
            super().__init__()
            self.term = term

    class EditRequested(Message):
        def __init__(self, term: str) -> None:
            super().__init__()
            self.term = term

    class DeleteRequested(Message):
        def __init__(self, term: str) -> None:
            super().__init__()
            self.term = term

    def __init__(self, entry: GlossaryEntry) -> None:
        super().__init__(classes="glossary-entry-item")
        self.can_focus = True
        self.entry = entry

    @property
    def term(self) -> str:
        return self.entry.term

    def compose(self) -> ComposeResult:
        with Horizontal(classes="glossary-entry-header"):
            yield Static(self.entry.term, classes="glossary-entry-term")
            yield EmptyWidget(classes="fill-space-horizontal")
            with Horizontal(classes="glossary-entry-actions"):
                yield Button("edit", classes="glossary-entry-edit", compact=True)
                yield Button("delete", classes="glossary-entry-delete", compact=True)
        yield Static(self.entry.description, classes="glossary-entry-description")

    def on_click(self, event: Click) -> None:
        event.stop()
        self.focus()
        self.post_message(self.Selected(self.entry.term))

    def on_focus(self) -> None:
        self.post_message(self.Selected(self.entry.term))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.has_class("glossary-entry-edit"):
            event.stop()
            self.post_message(self.EditRequested(self.entry.term))
            return

        if event.button.has_class("glossary-entry-delete"):
            event.stop()
            self.post_message(self.DeleteRequested(self.entry.term))


class GlossaryList(VerticalScroll):
    def __init__(self, entries: tuple[GlossaryEntry, ...], *, id: str | None = None) -> None:
        super().__init__(id=id)
        self.entries = entries

    def compose(self) -> ComposeResult:
        for entry in self.entries:
            yield GlossaryEntryWidget(entry)
