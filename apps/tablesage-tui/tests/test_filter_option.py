from __future__ import annotations

import asyncio

from tablesage_tui.widgets import FilterOption
from textual.app import App, ComposeResult


class _Host(App[None]):
    def __init__(self) -> None:
        super().__init__()
        self.selected_filter_name: str | None = None

    def compose(self) -> ComposeResult:
        yield FilterOption("active", 3, id="active-filter")

    def on_filter_option_selected(self, event: FilterOption.Selected) -> None:
        self.selected_filter_name = event.filter_name


def test_filter_option_renders_name_and_count() -> None:
    option = FilterOption("all", 8, selected=True)

    assert str(option.render()) == "all (8)"
    assert option.has_class("-selected")


def test_filter_option_click_selects_and_posts_message() -> None:
    async def scenario() -> None:
        app = _Host()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#active-filter")
            await pilot.pause()

            option = app.query_one("#active-filter", FilterOption)
            assert option.selected is True
            assert option.has_class("-selected")
            assert app.selected_filter_name == "active"

    asyncio.run(scenario())
