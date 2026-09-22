from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static

from .command_button import CommandButton


class ProcessingStepControl(Horizontal):
    """One processing step, with reserved keybinding and completion columns.

    Hosts handle ``Activated`` and route their screen bindings to ``press()``;
    this keeps shortcut ownership and conflicts with the containing screen.
    The key slot is reserved even when no binding is supplied. All four values
    are reactive.
    """

    is_complete = reactive(False)
    is_enabled = reactive(True)
    keybinding: reactive[str | None] = reactive(None)
    entry_text = reactive("")

    class Activated(Message):
        """The enabled entry's command was activated."""

        def __init__(self, step: ProcessingStepControl) -> None:
            super().__init__()
            self.step = step

    def __init__(
        self,
        is_complete: bool = False,
        is_enabled: bool = True,
        keybinding: str | None = None,
        entry_text: str = "",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.is_complete = is_complete
        self.is_enabled = is_enabled
        self.keybinding = keybinding
        self.entry_text = entry_text

    def compose(self) -> ComposeResult:
        with CommandButton(classes="command-entry-binding"):
            yield Static("", classes="keycap", markup=False)
        yield Static("", classes="command-entry-complete", markup=False)
        yield Static("", classes="command-entry-text", markup=False)

    def on_mount(self) -> None:
        self._sync_state()

    def watch_is_complete(self) -> None:
        self._sync_state()

    def watch_is_enabled(self) -> None:
        self._sync_state()

    def watch_keybinding(self) -> None:
        self._sync_state()

    def watch_entry_text(self) -> None:
        self._sync_state()

    def _sync_state(self) -> None:
        if not self.children:
            return
        binding = (self.keybinding or "").strip()
        button = self.query_one(CommandButton)
        # Visibility reserves the column, unlike display: none.
        button.styles.visibility = "visible" if binding else "hidden"
        button.disabled = not self.is_enabled or not binding
        button.query_one(Static).update(binding)
        self.query_one(".command-entry-complete", Static).update("✓" if self.is_complete else "")
        self.query_one(".command-entry-text", Static).update(self.entry_text)
        self.set_class(not self.is_enabled, "-unavailable")

    def press(self) -> None:
        """Activate through the same path as clicking the keycap."""
        if self.is_enabled and (self.keybinding or "").strip():
            self.query_one(CommandButton).press()

    def on_command_button_pressed(self, event: CommandButton.Pressed) -> None:
        event.stop()
        if self.is_enabled and (self.keybinding or "").strip():
            self.post_message(self.Activated(self))
