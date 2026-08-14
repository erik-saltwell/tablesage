from __future__ import annotations

from typing import Self

from textual import events
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Static


class FilterOption(Static):
    BINDINGS = [
        Binding("enter,space", "select", "Select", show=False),
    ]
    can_focus = True

    selected = reactive(False)

    class Selected(Message):
        def __init__(self, option: FilterOption) -> None:
            self.option = option
            super().__init__()

        @property
        def filter_name(self) -> str:
            return self.option.filter_name

    def __init__(
        self,
        filter_name: str,
        count: int,
        *,
        selected: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ) -> None:
        self.filter_name = filter_name
        self.count = count
        super().__init__(
            self._label,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self.selected = selected

    @property
    def _label(self) -> str:
        return f"{self.filter_name} ({self.count})"

    def watch_selected(self) -> None:
        self.set_class(self.selected, "-selected")

    def select(self) -> Self:
        if self.disabled or self.selected:
            return self

        self.selected = True
        self.post_message(self.Selected(self))
        return self

    def action_select(self) -> None:
        self.select()

    def on_click(self, event: events.Click) -> None:
        event.stop()
        self.select()
