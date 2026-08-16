import pytest
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.widgets import CommandButton
from textual.widgets import Static


@pytest.mark.anyio
async def test_first_campaign_call_to_action_uses_command_button() -> None:
    async with TableSageApp().run_test() as pilot:
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
    async with TableSageApp().run_test() as pilot:
        button = pilot.app.screen.query_one("#start-campaign-command", CommandButton)

        assert not button.has_focus

        await pilot.press("tab")

        assert button.has_focus
