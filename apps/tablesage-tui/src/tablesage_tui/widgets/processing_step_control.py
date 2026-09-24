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
    The key slot is reserved even when no binding is supplied. All five values
    are reactive.

    A skipped step does not apply to this Session: it is shown struck through and
    dimmed, and cannot be activated, independently of whether it is enabled.
    """

    is_complete = reactive(False)
    is_enabled = reactive(True)
    is_skipped = reactive(False)
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
        is_skipped: bool = False,
        keybinding: str | None = None,
        entry_text: str = "",
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.is_complete = is_complete
        self.is_enabled = is_enabled
        self.is_skipped = is_skipped
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

    def watch_is_skipped(self) -> None:
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
        button.disabled = not self.can_activate
        button.query_one(Static).update(binding)
        self.query_one(".command-entry-complete", Static).update("✓" if self.is_complete else "")
        self.query_one(".command-entry-text", Static).update(self.entry_text)
        self.set_class(not self.is_enabled or self.is_skipped, "-unavailable")
        self.set_class(self.is_skipped, "-skipped")

    @property
    def can_activate(self) -> bool:
        """Whether ``press()`` would activate the step."""
        return self.is_enabled and not self.is_skipped and bool((self.keybinding or "").strip())

    def press(self) -> None:
        """Activate through the same path as clicking the keycap."""
        if self.can_activate:
            self.query_one(CommandButton).press()

    def on_command_button_pressed(self, event: CommandButton.Pressed) -> None:
        event.stop()
        if self.can_activate:
            self.post_message(self.Activated(self))
