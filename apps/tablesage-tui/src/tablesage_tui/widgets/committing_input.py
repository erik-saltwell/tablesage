from __future__ import annotations

from textual import events
from textual.message import Message
from textual.widgets import Input


class CommittingInput(Input):
    """An `Input` that announces a commit point: Enter, or losing focus.

    Used by inline metadata forms (composite screens) where there is no
    separate "save" action — typing directly edits the field, and the value
    should persist as soon as the user moves on, not only on Enter.
    """

    class Committed(Message):
        def __init__(self, input: CommittingInput) -> None:
            self.input = input
            super().__init__()

    def _on_blur(self, event: events.Blur) -> None:
        super()._on_blur(event)
        self.post_message(self.Committed(self))
