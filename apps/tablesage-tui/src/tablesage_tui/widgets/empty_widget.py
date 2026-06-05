from __future__ import annotations

from textual.widgets import Static


class EmptyWidget(Static):
    """A blank Static widget for intentional empty space."""

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ) -> None:
        super().__init__(
            "",
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
