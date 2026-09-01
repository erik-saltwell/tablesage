from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Static

from ..widgets import EqualWidthButtonRow


@dataclass(frozen=True)
class FindReplaceResult:
    find: str
    replace: str
    case_sensitive: bool


class FindReplaceDialog(ModalScreen[FindReplaceResult | None]):
    """Ask for a find string, a replacement string, and whether the search is case sensitive.

    Neither field is trimmed -- a search or replacement built entirely of whitespace is valid
    (e.g. collapsing a double space). `find` blank disables submission; `replace` may be blank
    (deletes every match).
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def compose(self) -> ComposeResult:
        with Vertical(id="find-replace-dialog") as dialog:
            dialog.border_title = "Find & Replace"
            with Horizontal(classes="field-row"):
                yield Static("Find", classes="field-label")
                yield Input(id="find-replace-find")
            with Horizontal(classes="field-row"):
                yield Static("Replace", classes="field-label")
                yield Input(id="find-replace-replace")
            yield Checkbox("Case sensitive", value=True, id="find-replace-case-sensitive")
            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Cancel", id="find-replace-cancel")
                yield Button("Replace All", id="find-replace-submit", variant="primary", disabled=True)

    def on_mount(self) -> None:
        self.query_one("#find-replace-find", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "find-replace-find":
            self.query_one("#find-replace-submit", Button).disabled = not event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "find-replace-cancel":
            self.dismiss(None)
        elif event.button.id == "find-replace-submit":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        if self.query_one("#find-replace-find", Input).value:
            self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        find = self.query_one("#find-replace-find", Input).value
        if not find:
            return
        replace = self.query_one("#find-replace-replace", Input).value
        case_sensitive = self.query_one("#find-replace-case-sensitive", Checkbox).value
        self.dismiss(FindReplaceResult(find=find, replace=replace, case_sensitive=case_sensitive))
