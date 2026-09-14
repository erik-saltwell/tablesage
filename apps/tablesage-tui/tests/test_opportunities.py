import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from tablesage_application.campaign_recap import CampaignSceneRecap
from tablesage_application.opportunities import Opportunity, OpportunityResult, OpportunitySet, generate, save
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.opportunities import OpportunitiesScreen
from textual.widgets import Button, Static, TextArea


def recap() -> CampaignSceneRecap:
    return CampaignSceneRecap(
        campaign_id=uuid.uuid4(), campaign_name="Campaign", starting_situation="Start", scenes=(), ending_situation="At the ferry"
    )


def result() -> OpportunityResult:
    return OpportunityResult(
        campaign_name="Campaign",
        prompt="Cross the river",
        pitches=OpportunitySet(
            opportunities=(Opportunity(title="A favor", from_campaign="Saved the ferryman", opportunity="Ask for passage"),)
        ),
    )


@pytest.mark.anyio
async def test_failure_preserves_results_and_save_uses_generating_prompt(tmp_path: Path) -> None:
    application = MagicMock()
    application.generate_opportunities.side_effect = [result(), ValueError("Generation failed")]
    async with TableSageApp(application).run_test() as pilot:
        screen = OpportunitiesScreen(recap())
        pilot.app.push_screen(screen)
        await pilot.pause()
        assert screen.query_one("#opportunity-generate", Button).disabled
        prompt = screen.query_one("#opportunity-prompt", TextArea)
        prompt.load_text("Cross the river")
        await pilot.pause()
        await pilot.press("ctrl+g")
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert screen.result == result()
        prompt.load_text("Visit the guild")
        await pilot.press("ctrl+g")
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert screen.result == result()
        assert "Generation failed" in str(screen.query_one("#opportunity-error", Static).render())
        screen._save(tmp_path / "seeds.md", overwrite=False)
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        application.save_opportunities.assert_called_once_with(result(), tmp_path / "seeds.md", overwrite=False)


def test_save_preserves_existing_file_and_exports_whole_set(tmp_path: Path) -> None:
    destination = tmp_path / "seeds.md"
    destination.write_text("existing")
    with pytest.raises(FileExistsError):
        save(result(), destination)
    assert destination.read_text() == "existing"
    save(result(), destination, overwrite=True)
    assert destination.read_text() == result().markdown()


@pytest.mark.anyio
async def test_generation_sends_complete_recap_and_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import AsyncMock

    from tablesage_application import opportunities

    call = AsyncMock(return_value=result().pitches.model_dump_json())
    monkeypatch.setattr(opportunities, "call_llm_with_prompt", call)
    history = recap()
    generated = await generate(history, "  Cross the river  ", "provider/model", 123)
    assert generated.prompt == "Cross the river"
    assert call.call_args.args[1].recap == history.model_dump_json()
    assert call.call_args.args[2] == "provider/model"
    assert call.call_args.kwargs["timeout"] == 123


def test_application_revalidates_history_and_uses_deployed_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import AsyncMock

    from tablesage_application import Application, opportunities
    from tablesage_model.settings import AppSettings

    app = Application(tmp_path, settings=AppSettings(llm_model_high="provider/model", opportunities_timeout=123))
    history = recap()
    loader = MagicMock(return_value=history)
    monkeypatch.setattr(app, "create_campaign_scene_recap", loader)
    generate_mock = AsyncMock(return_value=result())
    monkeypatch.setattr(opportunities, "generate", generate_mock)
    assert app.generate_opportunities(history.campaign_id, "Cross the river") == result()
    generate_mock.assert_awaited_once_with(history, "Cross the river", "provider/model", 123)
    loader.side_effect = ValueError("Scene Breakdown is stale")
    with pytest.raises(ValueError, match="stale"):
        app.generate_opportunities(history.campaign_id, "Cross the river")
    assert generate_mock.await_count == 1


@pytest.mark.anyio
async def test_context_limit_is_reported_without_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import AsyncMock

    from litellm.exceptions import ContextWindowExceededError
    from tablesage_application import opportunities

    call = AsyncMock(side_effect=ContextWindowExceededError("too long", "provider/model", "provider"))
    monkeypatch.setattr(opportunities, "call_llm_with_prompt", call)
    with pytest.raises(ValueError, match="Campaign is too large"):
        await generate(recap(), "Cross the river", "provider/model", 123)
    assert call.await_count == 1
