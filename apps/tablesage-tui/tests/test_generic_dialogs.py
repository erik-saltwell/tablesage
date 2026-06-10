from __future__ import annotations

import asyncio

from tablesage_tui.dialogs import ConfirmationDialog, TextInputDialog
from textual.app import App
from textual.widgets import Input


class _ConfirmationHost(App[None]):
    def __init__(self, dialog: ConfirmationDialog) -> None:
        super().__init__()
        self._dialog = dialog
        self.result: bool | None | str = "UNSET"

    def on_mount(self) -> None:
        self.push_screen(self._dialog, self._capture)

    def _capture(self, result: bool | None) -> None:
        self.result = result


class _TextInputHost(App[None]):
    def __init__(self, dialog: TextInputDialog) -> None:
        super().__init__()
        self._dialog = dialog
        self.result: str | None | object = object()

    def on_mount(self) -> None:
        self.push_screen(self._dialog, self._capture)

    def _capture(self, result: str | None) -> None:
        self.result = result


def test_confirmation_yes_dismisses_with_true() -> None:
    async def scenario() -> None:
        app = _ConfirmationHost(ConfirmationDialog(title="Delete Player", prompt="Delete Erik?"))
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#confirmation-yes")
            await pilot.pause()

            assert app.result is True

    asyncio.run(scenario())


def test_confirmation_no_dismisses_with_false() -> None:
    async def scenario() -> None:
        app = _ConfirmationHost(ConfirmationDialog(title="Delete Player", prompt="Delete Erik?"))
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#confirmation-no")
            await pilot.pause()

            assert app.result is False

    asyncio.run(scenario())


def test_confirmation_can_hide_cancel_button() -> None:
    async def scenario() -> None:
        app = _ConfirmationHost(ConfirmationDialog(title="Delete Player", prompt="Delete Erik?", show_cancel=False))
        async with app.run_test() as pilot:
            await pilot.pause()

            assert not list(app.screen.query("#confirmation-cancel"))

    asyncio.run(scenario())


def test_text_input_yes_dismisses_with_trimmed_value() -> None:
    async def scenario() -> None:
        app = _TextInputHost(TextInputDialog(title="New Player", prompt="Name of new player:"))
        async with app.run_test() as pilot:
            await pilot.pause()
            app.screen.query_one("#text-input-value", Input).value = "  Erik  "
            await pilot.click("#text-input-yes")
            await pilot.pause()

            assert app.result == "Erik"

    asyncio.run(scenario())


def test_text_input_no_dismisses_with_none() -> None:
    async def scenario() -> None:
        app = _TextInputHost(TextInputDialog(title="New Player", prompt="Name of new player:"))
        async with app.run_test() as pilot:
            await pilot.pause()
            app.screen.query_one("#text-input-value", Input).value = "Erik"
            await pilot.click("#text-input-no")
            await pilot.pause()

            assert app.result is None

    asyncio.run(scenario())


def test_text_input_uses_configured_placeholder() -> None:
    async def scenario() -> None:
        app = _TextInputHost(
            TextInputDialog(
                title="New Player",
                prompt="Name of new player:",
                placeholder="Ada Lovelace",
            )
        )
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.screen.query_one("#text-input-value", Input).placeholder == "Ada Lovelace"

    asyncio.run(scenario())
