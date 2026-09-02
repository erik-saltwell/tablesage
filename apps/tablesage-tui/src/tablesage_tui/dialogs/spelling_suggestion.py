from __future__ import annotations

from dataclasses import dataclass

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Static

from ..widgets import EqualWidthButtonRow


@dataclass(frozen=True)
class SpellingSuggestionResult:
    from_text: str
    to_text: str
    case_sensitive: bool


class SpellingSuggestionDialog(ModalScreen[SpellingSuggestionResult | None]):
    """Add or edit one spelling-correction suggestion row: a `from` snippet, its `to` replacement, and case sensitivity.

    Same three-field shape as `FindReplaceDialog`, but defaults `case_sensitive` to False (that
    dialog defaults to True) -- the ASR mishearings this feature targets often differ only in
    case, and unlike an ad hoc Find & Replace this is reviewed as an accept/edit/delete decision
    per row, not fired once and forgotten.
    """

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(
        self,
        *,
        title: str,
        submit_label: str,
        from_text: str = "",
        to_text: str = "",
        case_sensitive: bool = False,
    ) -> None:
        super().__init__()
        self._title = title
        self._submit_label = submit_label
        self._from_text = from_text
        self._to_text = to_text
        self._case_sensitive = case_sensitive

    def compose(self) -> ComposeResult:
        with Vertical(id="spelling-suggestion-dialog") as dialog:
            dialog.border_title = self._title
            with Horizontal(classes="field-row"):
                yield Static("From", classes="field-label")
                yield Input(value=self._from_text, id="spelling-suggestion-from")
            with Horizontal(classes="field-row"):
                yield Static("To", classes="field-label")
                yield Input(value=self._to_text, id="spelling-suggestion-to")
            yield Checkbox("Case sensitive", value=self._case_sensitive, id="spelling-suggestion-case-sensitive")
            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Cancel", id="spelling-suggestion-cancel")
                yield Button(self._submit_label, id="spelling-suggestion-submit", variant="primary", disabled=not self._from_text)

    def on_mount(self) -> None:
        self.query_one("#spelling-suggestion-from", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "spelling-suggestion-from":
            self.query_one("#spelling-suggestion-submit", Button).disabled = not event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "spelling-suggestion-cancel":
            self.dismiss(None)
        elif event.button.id == "spelling-suggestion-submit":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        if self.query_one("#spelling-suggestion-from", Input).value:
            self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        from_text = self.query_one("#spelling-suggestion-from", Input).value
        if not from_text:
            return
        to_text = self.query_one("#spelling-suggestion-to", Input).value
        case_sensitive = self.query_one("#spelling-suggestion-case-sensitive", Checkbox).value
        self.dismiss(SpellingSuggestionResult(from_text=from_text, to_text=to_text, case_sensitive=case_sensitive))
