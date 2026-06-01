from __future__ import annotations

from os import PathLike
from typing import Self

from textual.widgets import Static

from ..resources import load_resource


class AsciiArt(Static):
    """Static widget for preformatted ASCII art."""

    def __init__(
        self,
        content: str = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            content,
            expand=expand,
            shrink=shrink,
            markup=False,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

    @classmethod
    def from_resource(
        cls,
        filepath: str | PathLike[str],
        *,
        encoding: str = "utf-8",
        expand: bool = False,
        shrink: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> Self:
        return cls(
            load_resource(filepath, encoding=encoding),
            expand=expand,
            shrink=shrink,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
