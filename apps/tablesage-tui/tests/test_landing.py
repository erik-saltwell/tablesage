from unittest.mock import MagicMock

import pytest
from tablesage_tui.dialogs import ConfirmationDialog
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.widgets import CommandButton
from textual.widgets import Button, Static


@pytest.mark.anyio
async def test_first_campaign_call_to_action_uses_command_button() -> None:
    async with TableSageApp(MagicMock()).run_test() as pilot:
        button = pilot.app.screen.query_one("#start-campaign-command", CommandButton)

        assert button.command_action == "new_campaign"
        assert [str(part.render()) for part in button.query(Static)] == [
            "> type ",
            "N",
            " to start your first campaign",
        ]

        await pilot.press("n")
        button.press()
        await pilot.pause()


@pytest.mark.anyio
async def test_first_campaign_call_to_action_is_not_initially_focused() -> None:
    async with TableSageApp(MagicMock()).run_test() as pilot:
        button = pilot.app.screen.query_one("#start-campaign-command", CommandButton)

        assert not button.has_focus

        await pilot.press("tab")

        assert button.has_focus


@pytest.mark.anyio
async def test_import_campaign_opens_confirmation_dialog() -> None:
    async with TableSageApp(MagicMock()).run_test() as pilot:
        await pilot.press("i")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmationDialog)
        assert pilot.app.screen.query_one("#confirmation-dialog").border_title == ("Import Campaign")
        assert str(pilot.app.screen.query_one("#confirmation-prompt", Static).render()) == ("Import an existing campaign?")
        buttons = list(pilot.app.screen.query(Button))
        assert [str(button.label) for button in buttons] == [
            "Cancel",
            "No",
            "Yes",
        ]
        assert len({button.region.width for button in buttons}) == 1
