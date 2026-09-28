from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import cast

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from ..widgets import CommandButton


class OtherActionButton(CommandButton):
    """A command-styled row that returns a binding action to its enclosing dialog."""

    def __init__(self, binding: Binding) -> None:
        super().__init__(binding.action, id=f"other-action-{binding.action.replace('(', '-').replace(')', '')}")
        self._binding = binding

    def compose(self) -> ComposeResult:
        yield Static(self._binding.key_display or self._binding.key.split(",", maxsplit=1)[0], classes="keycap")
        yield Static(self._binding.description, classes="other-action-description")

    def press(self) -> OtherActionButton:
        if self.disabled:
            return self
        cast(OtherActionsDialog, self.screen).dismiss(self._binding.action)
        return self


class OtherActionsDialog(ModalScreen[str | None]):
    """A screen's secondary bindings as a keyboard- and pointer-accessible menu."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=False)]

    def __init__(self, bindings: Sequence[Binding], *, disabled_actions: Collection[str] = ()) -> None:
        super().__init__()
        self._other_bindings = tuple(bindings)
        self._disabled_actions = frozenset(disabled_actions)
        self._actions_by_key = {
            key.casefold(): binding.action
            for binding in self._other_bindings
            for key in binding.key.split(",")
            if key.casefold() not in {"enter", "space", "escape"}
        }

    def compose(self) -> ComposeResult:
        with Vertical(id="other-actions-dialog") as dialog:
            dialog.border_title = " Other actions "
            yield Static("Choose an action", classes="other-actions-prompt")
            with Vertical(id="other-actions-list"):
                for binding in self._other_bindings:
                    button = OtherActionButton(binding)
                    button.disabled = binding.action in self._disabled_actions
                    yield button

    def on_mount(self) -> None:
        for button in self.query(OtherActionButton):
            if not button.disabled:
                button.focus()
                break

    def on_key(self, event: events.Key) -> None:
        action = self._actions_by_key.get(event.key.casefold())
        if action is None:
            return
        event.stop()
        if action in self._disabled_actions:
            return
        self.dismiss(action)

    def action_cancel(self) -> None:
        self.dismiss(None)
