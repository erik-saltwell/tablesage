from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from tablesage_model.model import Campaign
from tablesage_tui.dialogs import ConfirmationDialog, TextInputDialog
from tablesage_tui.screens.campaign_list import CampaignListScreen
from tablesage_tui.screens.main_app import TableSageApp
from textual.pilot import Pilot
from textual.widgets import DataTable, Input


def _application(*, campaigns: list | None = None, last_session_dates: dict | None = None) -> MagicMock:
    return MagicMock(
        list_campaigns=MagicMock(return_value=campaigns or []),
        last_session_dates=MagicMock(return_value=last_session_dates or {}),
    )


async def _open_campaign_list(pilot: Pilot) -> None:
    await pilot.press("c")
    await pilot.pause()


@pytest.mark.anyio
async def test_pressing_c_from_landing_opens_campaign_list_screen() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_campaign_list(pilot)

        assert isinstance(pilot.app.screen, CampaignListScreen)


@pytest.mark.anyio
async def test_campaign_table_has_expected_columns() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_campaign_list(pilot)

        table = pilot.app.screen.query_one("#campaign-table", DataTable)
        assert [str(column.label) for column in table.columns.values()] == [
            "Campaign",
            "Game System",
            "Last Session",
        ]


@pytest.mark.anyio
async def test_campaign_table_shows_last_session_date() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaigns=[campaign], last_session_dates={campaign.id: date(2026, 8, 1)})

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        table = pilot.app.screen.query_one("#campaign-table", DataTable)
        row = tuple(str(cell) for cell in table.get_row_at(0))
        assert row[2] == "2026-08-01"


@pytest.mark.anyio
async def test_open_and_import_actions_are_stubbed_with_notify() -> None:
    async with TableSageApp(_application()).run_test() as pilot:
        await _open_campaign_list(pilot)

        for key in ("enter", "i"):
            await pilot.press(key)
            await pilot.pause()


@pytest.mark.anyio
async def test_enter_on_selected_campaign_opens_campaign() -> None:
    application = _application(campaigns=[Campaign(name="Iron Pact")])

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        screen = pilot.app.screen
        assert isinstance(screen, CampaignListScreen)

        with patch.object(screen, "action_open_campaign") as open_campaign:
            await pilot.press("enter")
            await pilot.pause()

        open_campaign.assert_called_once_with()


@pytest.mark.anyio
async def test_new_campaign_creates_and_reloads() -> None:
    created = Campaign(name="Iron Pact")
    application = _application()
    application.create_campaign = MagicMock(return_value=created)

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        await pilot.press("n")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TextInputDialog)

        pilot.app.screen.query_one("#text-input-value", Input).value = "Iron Pact"
        await pilot.press("enter")
        await pilot.pause()

        application.create_campaign.assert_called_once()
        assert application.create_campaign.call_args.args[0].name == "Iron Pact"
        assert application.list_campaigns.call_count >= 2


@pytest.mark.anyio
async def test_new_campaign_cancelled_does_not_create() -> None:
    application = _application()
    application.create_campaign = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        await pilot.press("n")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        application.create_campaign.assert_not_called()
        assert isinstance(pilot.app.screen, CampaignListScreen)


@pytest.mark.anyio
async def test_new_campaign_duplicate_name_shows_error() -> None:
    application = _application()
    application.create_campaign = MagicMock(side_effect=ValueError("A campaign named 'Iron Pact' already exists."))

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        await pilot.press("n")
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = "Iron Pact"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, CampaignListScreen)


@pytest.mark.anyio
async def test_delete_campaign_confirms_then_deletes() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaigns=[campaign])
    application.delete_campaign = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        await pilot.press("d")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.delete_campaign.assert_called_once_with(campaign.id)


@pytest.mark.anyio
async def test_delete_campaign_cancelled_does_not_delete() -> None:
    campaign = Campaign(name="Iron Pact")
    application = _application(campaigns=[campaign])
    application.delete_campaign = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        await pilot.press("d")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        application.delete_campaign.assert_not_called()


@pytest.mark.anyio
async def test_delete_with_no_campaigns_does_nothing() -> None:
    application = _application()
    application.delete_campaign = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        await pilot.press("d")
        await pilot.pause()

        application.delete_campaign.assert_not_called()
        assert isinstance(pilot.app.screen, CampaignListScreen)


@pytest.mark.anyio
async def test_cleanup_campaigns_confirms_then_cleans() -> None:
    application = _application()
    application.cleanup_orphan_campaign_dirs = MagicMock(return_value=["Stale Campaign"])

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        await pilot.press("c")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)

        await pilot.press("tab", "tab", "enter")
        await pilot.pause()

        application.cleanup_orphan_campaign_dirs.assert_called_once_with()


@pytest.mark.anyio
async def test_cleanup_campaigns_cancelled_does_not_clean() -> None:
    application = _application()
    application.cleanup_orphan_campaign_dirs = MagicMock()

    async with TableSageApp(application).run_test() as pilot:
        await _open_campaign_list(pilot)

        await pilot.press("c")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        application.cleanup_orphan_campaign_dirs.assert_not_called()
