import pytest
from tablesage_tui.widgets import EqualWidthButtonRow
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button


class _Screen(Screen[None]):
    def __init__(self, *, hidden: bool) -> None:
        super().__init__()
        self._hidden = hidden

    def compose(self) -> ComposeResult:
        with Vertical(id="panel") as panel:
            panel.display = not self._hidden
            with EqualWidthButtonRow(id="actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Apply & Continue", id="complete", variant="primary")


class _HostApp(App[None]):
    def __init__(self, *, hidden: bool) -> None:
        super().__init__()
        self._hidden = hidden

    def get_default_screen(self) -> Screen[None]:
        return _Screen(hidden=self._hidden)


async def _button_widths(hidden: bool) -> dict[str, int]:
    async with _HostApp(hidden=hidden).run_test() as pilot:
        screen = pilot.app.screen
        widths: dict[str, int] = {}
        for button in screen.query(Button):
            assert button.id is not None
            assert button.styles.width is not None
            widths[button.id] = int(button.styles.width.value)
        return widths


@pytest.mark.anyio
async def test_equal_width_fits_the_longest_label_when_visible_at_mount() -> None:
    widths = await _button_widths(hidden=False)
    # "Apply & Continue" is 16 characters; the button needs at least 18 (2 border cells) to
    # avoid clipping, and both buttons must match since the row equalizes them.
    assert widths["cancel"] == widths["complete"]
    assert widths["cancel"] >= 18


@pytest.mark.anyio
async def test_equal_width_fits_the_longest_label_even_when_hidden_at_mount() -> None:
    """Regression test: a row inside a `display: none` container (e.g. one of Manual Review's
    two phase panels, shown later by toggling `display`) must still size itself off each
    button's real label, not off `region.width`, which reads 0 for anything never laid out --
    `min-width: 8` would otherwise floor every button in the row to the same too-small width."""
    widths = await _button_widths(hidden=True)
    assert widths["cancel"] == widths["complete"]
    assert widths["cancel"] >= 18
