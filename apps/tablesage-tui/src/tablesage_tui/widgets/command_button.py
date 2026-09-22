from __future__ import annotations

from typing import Self

from textual import events
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget


class CommandButton(Horizontal):
    class Pressed(Message):
        """An actionless command button was activated."""

        def __init__(self, button: CommandButton) -> None:
            super().__init__()
            self.button = button

    BINDINGS = [
        Binding("enter,space", "press", "Press", show=False),
    ]
    can_focus = True
    active_effect_duration = 0.12

    def __init__(
        self,
        action: str | None = None,
        *children: Widget,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ) -> None:
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.command_action = action

    def press(self) -> Self:
        if self.disabled or not self.display or not self.visible or self.has_class("-active"):
            return self

        self.add_class("-active")
        self.set_timer(self.active_effect_duration, self._clear_active)
        if self.command_action is None:
            self.post_message(self.Pressed(self))
        else:
            self.call_later(
                self.app.run_action,
                self.command_action,
                default_namespace=self.screen,
            )
        return self

    def action_press(self) -> None:
        self.press()

    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.press()

    def _clear_active(self) -> None:
        self.remove_class("-active")
