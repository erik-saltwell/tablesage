import uuid
from unittest.mock import MagicMock, patch

import pytest
from tablesage_model.model import Player
from tablesage_tui.dialogs.other_actions import OtherActionButton, OtherActionsDialog
from tablesage_tui.screens.base import TableSageScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.player_detail import PlayerDetailScreen
from textual.app import ComposeResult
from textual.binding import Binding
from textual.pilot import Pilot
from textual.widgets import Footer, Static


class SecondaryActionScreen(TableSageScreen):
    COMMON_BINDINGS = [Binding("p", "primary", "Primary", key_display="P")]
    OTHER_BINDINGS = [Binding("o", "secondary", "Secondary", key_display="O")]

    def __init__(self) -> None:
        self.secondary_runs = 0
        super().__init__()

    def compose_content(self) -> ComposeResult:
        yield Static("Test screen")

    def action_primary(self) -> None:
        pass

    def action_secondary(self) -> None:
        self.secondary_runs += 1


async def _open_player_detail(pilot: Pilot, player_id: uuid.UUID) -> None:
    pilot.app.push_screen(PlayerDetailScreen(player_id))
    await pilot.pause()


@pytest.mark.anyio
async def test_other_actions_dialog_dispatches_a_secondary_binding_after_dismissal() -> None:
    async with TableSageApp(MagicMock()).run_test() as pilot:
        screen = SecondaryActionScreen()
        pilot.app.push_screen(screen)
        await pilot.pause()

        assert screen.query_one(Footer).has_class("-has-other-actions")

        await pilot.press("slash")
        await pilot.pause()

        dialog = pilot.app.screen
        assert isinstance(dialog, OtherActionsDialog)
        button = dialog.query_one(OtherActionButton)
        assert button.query_one(".keycap", Static).render() == "O"
        assert button.query_one(".other-action-description", Static).render() == "Secondary"

        await pilot.press("o")
        await pilot.pause()

        assert pilot.app.screen is screen
        assert screen.secondary_runs == 1


@pytest.mark.anyio
async def test_other_actions_dialog_runs_the_focused_row_with_enter() -> None:
    async with TableSageApp(MagicMock()).run_test() as pilot:
        screen = SecondaryActionScreen()
        pilot.app.push_screen(screen)
        await pilot.pause()

        await pilot.press("question_mark")
        await pilot.press("enter")
        await pilot.pause()

        assert pilot.app.screen is screen
        assert screen.secondary_runs == 1


@pytest.mark.anyio
async def test_run_with_progress_success_is_deferred_via_call_after_refresh() -> None:
    """Regression guard: `on_worker_state_changed` must hand `on_success` to `call_after_refresh`,
    not call it inline. Calling it inline lets a widget mutation (e.g. reloading a list) race the
    ProgressDialog pop's own screen-transition render, which can leave stale content on screen
    until something else forces a repaint -- see `TableSageScreen.run_with_progress`'s docstring."""
    player = Player(name="Alice")
    application = MagicMock(get_player=MagicMock(return_value=player), list_voice_clips=MagicMock(return_value=[]))
    application.recompute_centroid = MagicMock(return_value=Player(id=player.id, name="Alice", sample_count=1))

    async with TableSageApp(application).run_test() as pilot:
        await _open_player_detail(pilot, player.id)

        with patch.object(TableSageScreen, "call_after_refresh", wraps=pilot.app.screen.call_after_refresh) as deferred:
            await pilot.press("r")
            await pilot.pause()
            await pilot.app.workers.wait_for_complete()
            await pilot.pause()

        deferred.assert_called_once()
        called_callback = deferred.call_args.args[0]
        screen = pilot.app.screen
        assert isinstance(screen, PlayerDetailScreen)
        assert called_callback == screen._after_recompute_centroid
