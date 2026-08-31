from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from tablesage_tools.speakers import UNASSIGNED_SPEAKER
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select, Static
from textual.widgets.select import NoSelection

from ..widgets import EqualWidthButtonRow


@dataclass(frozen=True)
class ManualReviewUtteranceResult:
    speaker: str
    text: str


class ManualReviewUtteranceDialog(ModalScreen[ManualReviewUtteranceResult | None]):
    """Edit the speaker and displayed text of one utterance in the review working copy."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, *, attendee_names: list[str], speaker: str, text: str) -> None:
        super().__init__()
        speakers = [UNASSIGNED_SPEAKER, *attendee_names]
        if speaker not in speakers:
            speakers.append(speaker)
        self._speakers = speakers
        self._speaker = speaker
        self._text = text

    def compose(self) -> ComposeResult:
        with Vertical(id="manual-review-utterance-dialog") as dialog:
            dialog.border_title = "Edit Utterance"
            with Horizontal(classes="field-row"):
                yield Static("Speaker", classes="field-label")
                yield Select[str](
                    [("Unassigned" if name == UNASSIGNED_SPEAKER else name, name) for name in self._speakers],
                    id="manual-review-speaker",
                    value=self._speaker,
                    allow_blank=False,
                )
            yield Static("Text", classes="field-label")
            yield Input(value=self._text, id="manual-review-text")
            with EqualWidthButtonRow(classes="dialog-actions"):
                yield Button("Cancel", id="manual-review-edit-cancel")
                yield Button("Save", id="manual-review-edit-save", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#manual-review-speaker", Select).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "manual-review-edit-cancel":
            self.dismiss(None)
        elif event.button.id == "manual-review-edit-save":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self._submit()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        text = self.query_one("#manual-review-text", Input).value.strip()
        if not text:
            self.notify("Utterance text cannot be blank.", severity="error")
            return
        selected = self.query_one("#manual-review-speaker", Select).value
        if isinstance(selected, NoSelection):
            return
        self.dismiss(ManualReviewUtteranceResult(speaker=cast(str, selected), text=text))
