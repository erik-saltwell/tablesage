import uuid
from unittest.mock import MagicMock, patch

import pytest
from tablesage_model.model import Player
from tablesage_tui.screens.base import TableSageScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.player_detail import PlayerDetailScreen
from textual.pilot import Pilot


async def _open_player_detail(pilot: Pilot, player_id: uuid.UUID) -> None:
    pilot.app.push_screen(PlayerDetailScreen(player_id))
    await pilot.pause()


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
