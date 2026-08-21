from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class TranscriptViewDialog(ModalScreen[None]):
    """Stage 4's "show me everything Speaker N said" view.

    There is no audio playback anywhere in this app, so the punctuated transcript text is
    the only signal the human reviewer has to judge a diarized speaker's identity.
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
    ]

    def __init__(self, *, speaker_id: str, text: str) -> None:
        super().__init__()
        self._speaker_id = speaker_id
        self._text = text

    def compose(self) -> ComposeResult:
        with Vertical(id="transcript-view-dialog") as dialog:
            dialog.border_title = f" {self._speaker_id} "
            with VerticalScroll(id="transcript-view-scroll"):
                yield Static(self._text or "(no dialogue captured)", id="transcript-view-text")
            yield Button("Close", id="transcript-view-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "transcript-view-close":
            self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
