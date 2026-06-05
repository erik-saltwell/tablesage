from __future__ import annotations

import asyncio

from tablesage_tui.dialogs.new_campaign import NewCampaignDialog, NewCampaignResult
from textual.app import App
from textual.widgets import Input, Static


class _Host(App[None]):
    """Minimal host that pushes the dialog and captures its dismissal result."""

    def __init__(self, existing_slugs: frozenset[str]) -> None:
        super().__init__()
        self._existing_slugs = existing_slugs
        self.result: NewCampaignResult | None | str = "UNSET"

    def on_mount(self) -> None:
        self.push_screen(NewCampaignDialog(existing_slugs=self._existing_slugs), self._capture)

    def _capture(self, result: NewCampaignResult | None) -> None:
        self.result = result


def _fill(app: _Host, name: str, system: str, default_gm: str) -> None:
    dialog = app.screen
    dialog.query_one("#campaign-name", Input).value = name
    dialog.query_one("#campaign-system", Input).value = system
    dialog.query_one("#campaign-default-gm", Input).value = default_gm


def test_duplicate_name_keeps_dialog_open_and_shows_error() -> None:
    async def scenario() -> None:
        app = _Host(existing_slugs=frozenset({"iron-pact"}))
        async with app.run_test() as pilot:
            await pilot.pause()
            _fill(app, name="Iron Pact", system="D&D 5e", default_gm="Ada")
            await pilot.click("#create")
            await pilot.pause()

            assert app.result == "UNSET", "dialog must not dismiss on a duplicate name"
            error = app.screen.query_one("#new-campaign-error", Static)
            assert "already exists" in str(error.render())

    asyncio.run(scenario())


def test_unique_name_dismisses_with_result() -> None:
    async def scenario() -> None:
        app = _Host(existing_slugs=frozenset({"iron-pact"}))
        async with app.run_test() as pilot:
            await pilot.pause()
            _fill(app, name="Sable Crown", system="D&D 5e", default_gm="Ada")
            await pilot.click("#create")
            await pilot.pause()

            assert app.result == NewCampaignResult(name="Sable Crown", system="D&D 5e", default_gm="Ada")

    asyncio.run(scenario())
