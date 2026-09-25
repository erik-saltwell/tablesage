from __future__ import annotations

import uuid
from contextlib import suppress
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application import Application
from tablesage_application.previously_on import (
    CampaignHistory,
    CampaignSession,
    Ingredient,
    Ingredients,
    Recommendation,
    ScoutResult,
)
from tablesage_application.session_pipeline.scene_breakdown import LedgerRange, Scene, SceneBreakdown
from tablesage_model.model import Campaign
from tablesage_tui.dialogs.file_picker import FileSave
from tablesage_tui.dialogs.generic import ConfirmationDialog
from tablesage_tui.screens.campaign_detail import CampaignDetailScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.previously_on import ChoiceTree, PreviouslyOnScreen
from textual.pilot import Pilot
from textual.widgets import Button, ContentSwitcher, Input, TextArea
from textual.worker import WorkerFailed
from textual_fspicker.parts.directory_navigation import DirectoryNavigation


def _application() -> tuple[MagicMock, CampaignHistory, Ingredients, ScoutResult]:
    history = CampaignHistory(
        campaign_name="Brandonsford",
        sessions=tuple(
            CampaignSession(
                sequence_number=index,
                breakdown=SceneBreakdown(
                    session_id=uuid.UUID(int=index),
                    session_name=f"Session {index}",
                    ledger_sha256="0" * 64,
                    starting_situation="In the woods",
                    ending_situation=f"Ending {index}",
                    scenes=[
                        Scene(
                            title=f"Scene {index}",
                            location="Woods",
                            participants=["George"],
                            situation="A warning",
                            outcome="The dragon is poisonous",
                            carry_forward=["Seek anti-venom"],
                            signature_detail="A twisted staff",
                            ledger_ranges=[LedgerRange(start_index=0, end_index=0)],
                        )
                    ],
                ),
            )
            for index in (1, 2)
        ),
        glossary=(),
    )
    refs = list(history.scene_catalog())
    ingredients = Ingredients(
        people_and_factions=(Ingredient(label="George", current_state="Warned of poison", sources=(refs[0],)),),
        threads_and_commitments=(),
        active_pressures=(),
        places_and_objects=(),
    )
    result = ScoutResult(recommendations=(Recommendation(source=refs[0], rationale="Private witch connection"),))
    app = MagicMock(spec=Application)
    app.get_campaign.return_value = Campaign(name=history.campaign_name)
    app.list_sessions.return_value = []
    app.list_glossary_entries.return_value = []
    app.previously_on_history.return_value = history
    app.previously_on_ingredients.return_value = ingredients
    app.previously_on_scout.return_value = result
    app.previously_on_destination.side_effect = lambda path: path
    return app, history, ingredients, result


async def _workers(pilot: Pilot) -> None:
    with suppress(WorkerFailed):
        await pilot.app.workers.wait_for_complete()
    # Let screen transition callbacks and Textual's button active effect finish.
    await pilot.pause(0.35)


@pytest.mark.anyio
async def test_launch_from_campaign_and_initial_entry_state() -> None:
    application, history, _ingredients, _result = _application()
    async with TableSageApp(application).run_test(size=(140, 46)) as pilot:
        campaign_screen = CampaignDetailScreen(uuid.uuid4())
        pilot.app.push_screen(campaign_screen)
        await pilot.pause()
        await pilot.press("escape", "slash", "v")
        await _workers(pilot)
        screen = pilot.app.screen
        assert isinstance(screen, PreviouslyOnScreen)
        assert screen.query_one("#previously-on-start", TextArea).text == "Ending 2"
        assert screen.query_one("#previously-on-scout", Button).disabled
        assert not screen._selected_ingredients
        assert len(screen.query_one("#previously-on-ingredients", ChoiceTree).root.children) == 4
        assert not screen.has_changes()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.screen is campaign_screen
    application.previously_on_ingredients.assert_called_once_with(history)


@pytest.mark.anyio
@pytest.mark.parametrize("failure", ["history", "ingredients"])
async def test_launch_failure_remains_on_campaign(failure: str) -> None:
    application, _history, _ingredients, _result = _application()
    getattr(application, f"previously_on_{failure}").side_effect = ValueError("Session 001: Regenerate All Outputs")
    async with TableSageApp(application).run_test() as pilot:
        screen = CampaignDetailScreen(uuid.uuid4())
        pilot.app.push_screen(screen)
        await pilot.pause()
        with patch.object(screen, "notify") as notify:
            screen.action_create_previously_on()
            await _workers(pilot)
            assert pilot.app.screen is screen
            notify.assert_called_once_with("Session 001: Regenerate All Outputs", severity="error")
    if failure == "history":
        application.previously_on_ingredients.assert_not_called()


@pytest.mark.anyio
async def test_ingredients_and_complete_catalog_selection_and_rescout() -> None:
    application, history, ingredients, result = _application()
    async with TableSageApp(application).run_test(size=(140, 46)) as pilot:
        screen = PreviouslyOnScreen(history, ingredients)
        pilot.app.push_screen(screen)
        await pilot.pause()
        tree = screen.query_one("#previously-on-ingredients", ChoiceTree)
        node = tree.root.children[0].children[0]
        tree.move_cursor(node)
        tree.focus()
        await pilot.pause()
        assert "Session 001" in screen.query_one("#previously-on-evidence", TextArea).text
        await pilot.press("space")
        await pilot.pause()
        assert screen._selected_ingredients == {0}
        assert not screen.query_one("#previously-on-scout", Button).disabled
        screen.query_one("#previously-on-start", TextArea).load_text("GM opening")
        await pilot.click("#previously-on-scout")
        await _workers(pilot)
        sent = application.previously_on_scout.call_args.args[0]
        assert sent.starting_situation == "GM opening"
        assert sent.selected_ingredients == ingredients.people_and_factions
        assert sent.upcoming_notes == ""
        catalog = screen.query_one("#previously-on-scenes", ChoiceTree)
        assert catalog.root.children[0].is_expanded
        assert not catalog.root.children[1].is_expanded
        assert screen._selected_scenes == {result.recommendations[0].source}
        old_node = catalog.root.children[0].children[0]
        catalog.move_cursor(old_node)
        await pilot.pause()
        assert "Private witch connection" in screen.query_one("#previously-on-scene-detail", TextArea).text
        assert "signature_detail" in screen.query_one("#previously-on-scene-detail", TextArea).text
        catalog.root.children[1].expand()
        await pilot.pause()
        catalog.move_cursor(catalog.root.children[1].children[0])
        catalog.focus()
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert len(screen._selected_scenes) == 2
        await pilot.click("#previously-on-back")
        await pilot.pause()
        assert screen.query_one("#previously-on-start", TextArea).text == "GM opening"
        assert screen._selected_ingredients == {0}
        await pilot.click("#previously-on-scout")
        await _workers(pilot)
        assert screen._selected_scenes == {result.recommendations[0].source}


@pytest.mark.anyio
@pytest.mark.parametrize("size", [(80, 24), (120, 36)])
async def test_empty_scout_manual_selection_and_compact_layout(size: tuple[int, int]) -> None:
    application, history, ingredients, _result = _application()
    async with TableSageApp(application).run_test(size=size) as pilot:
        screen = PreviouslyOnScreen(history, ingredients)
        pilot.app.push_screen(screen)
        await pilot.pause()
        screen._show_selection(ScoutResult(recommendations=()))
        await pilot.pause()
        assert screen.query_one("#previously-on-save", Button).disabled
        tree = screen.query_one("#previously-on-scenes", ChoiceTree)
        assert all(not node.is_expanded for node in tree.root.children)
        tree.move_cursor(tree.root.children[0])
        tree.focus()
        await pilot.press("enter", "down", "space")
        await pilot.pause()
        assert len(screen._selected_scenes) == 1
        assert not screen.query_one("#previously-on-save", Button).disabled
        await pilot.press("space")
        await pilot.pause()
        assert screen.query_one("#previously-on-save", Button).disabled
        screen._save_failed(RuntimeError("Provider unavailable"))
        await pilot.pause()
        for selector in ("#previously-on-back", "#previously-on-exit-selection", "#previously-on-retry", "#previously-on-save"):
            assert screen.region.contains_region(screen.query_one(selector).region)


@pytest.mark.anyio
async def test_notes_only_scout_failure_preserves_inputs_and_allows_manual_retry() -> None:
    application, history, ingredients, result = _application()
    application.previously_on_scout.side_effect = [RuntimeError("Scout unavailable"), result]
    async with TableSageApp(application).run_test(size=(140, 46)) as pilot:
        screen = PreviouslyOnScreen(history, ingredients)
        pilot.app.push_screen(screen)
        await pilot.pause()
        screen.query_one("#previously-on-notes", TextArea).load_text("Visit the witch")
        await pilot.pause()
        await pilot.click("#previously-on-scout")
        await _workers(pilot)
        assert screen.query_one("#previously-on-stage", ContentSwitcher).current == "previously-on-entry"
        assert screen.query_one("#previously-on-notes", TextArea).text == "Visit the witch"
        assert screen.query_one("#previously-on-error").display
        await pilot.click("#previously-on-scout")
        await _workers(pilot)
        assert screen.query_one("#previously-on-stage", ContentSwitcher).current == "previously-on-selection"


@pytest.mark.anyio
async def test_save_cancel_overwrite_failure_retry_and_return(tmp_path: Path) -> None:
    application, history, ingredients, result = _application()
    target = tmp_path / "recap.md"
    target.write_text("Existing")
    application.export_previously_on.side_effect = [RuntimeError("Provider unavailable"), None]
    async with TableSageApp(application).run_test(size=(140, 46)) as pilot:
        campaign_screen = CampaignDetailScreen(uuid.uuid4())
        pilot.app.push_screen(campaign_screen)
        await pilot.pause()
        screen = PreviouslyOnScreen(history, ingredients)
        pilot.app.push_screen(screen)
        await pilot.pause()
        screen._show_selection(result)
        await pilot.pause()
        await pilot.click("#previously-on-save")
        await pilot.pause()
        assert isinstance(pilot.app.screen, FileSave)
        assert pilot.app.screen.query_one(Input).value == "Brandonsford-003-previously-on.md"
        assert pilot.app.screen.query_one(DirectoryNavigation).location == Path.home()
        pilot.app.screen.dismiss(None)
        await pilot.pause()
        assert pilot.app.screen is screen
        assert len(screen._selected_scenes) == 1
        application.export_previously_on.assert_not_called()
        await pilot.click("#previously-on-save")
        await pilot.pause()
        pilot.app.screen.dismiss(target)
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)
        application.export_previously_on.assert_not_called()
        await pilot.click("#confirmation-no")
        await pilot.pause()
        application.export_previously_on.assert_not_called()
        screen._destination_picked(target)
        await pilot.pause()
        await pilot.click("#confirmation-yes")
        await _workers(pilot)
        assert pilot.app.screen is screen
        assert screen._destination == target
        assert len(screen._selected_scenes) == 1
        assert screen.query_one("#previously-on-retry", Button).display
        await pilot.click("#previously-on-retry")
        await _workers(pilot)
        assert pilot.app.screen is campaign_screen
        assert application.export_previously_on.call_count == 2
        data = application.export_previously_on.call_args.args[0]
        assert set(type(data).model_fields) == {"selected_scenes", "starting_situation", "glossary"}
        assert application.export_previously_on.call_args.kwargs == {"overwrite": True}


@pytest.mark.anyio
@pytest.mark.parametrize("key", ["escape", "ctrl+q"])
async def test_dirty_exit_and_quit_require_confirmation(key: str) -> None:
    application, history, ingredients, _result = _application()
    async with TableSageApp(application).run_test(size=(140, 46)) as pilot:
        screen = PreviouslyOnScreen(history, ingredients)
        pilot.app.push_screen(screen)
        await pilot.pause()
        screen.query_one("#previously-on-notes", TextArea).load_text("Private notes")
        await pilot.pause()
        await pilot.press(key)
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmationDialog)
        await pilot.click("#confirmation-no")
        await pilot.pause()
        assert pilot.app.screen is screen
        assert screen.query_one("#previously-on-notes", TextArea).text == "Private notes"
        await pilot.press("escape")
        await pilot.pause()
        await pilot.click("#confirmation-yes")
        await pilot.pause()
        assert pilot.app.screen is not screen
